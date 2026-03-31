"""
Price monitoring scheduler.
Runs every 30 minutes to check tracked indices and send alerts.
Also syncs TW ETF list from TWSE daily at 01:00 Asia/Taipei.
Supports RSI-based and composite trigger conditions.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import get_supabase
from app.services.market_data import get_current_price
from app.services.email_service import send_email, build_alert_email
from app.services.line_service import send_line_message, build_alert_message
from app.services.tw_etf_sync import sync_tw_etf_list
from app.services.us_etf_sync import sync_us_etf_list
from app.services.news_briefing_service import run_market_briefing_session
from app.services.dividend_sync import sync_dividend_calendar
from app.services.dividend_notify_service import check_and_send_dividend_notifications
from app.services.rsi_service import get_rsi_calculation_service

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Taipei")


# ─── Trigger Condition Evaluation Functions ──────────────────────────────────

def _check_price_condition(
    current_price: float,
    trigger_price: float,
    trigger_direction: str
) -> bool:
    """
    檢查價格是否滿足觸發條件.
    
    Args:
        current_price: 當前價格
        trigger_price: 觸發價格閾值
        trigger_direction: 觸發方向 ("above" 或 "below")
    
    Returns:
        滿足條件返回 True
    """
    if trigger_direction == "above":
        return current_price >= trigger_price
    elif trigger_direction == "below":
        return current_price <= trigger_price
    return False


def _check_rsi_condition(
    current_rsi: Optional[float],
    rsi_below: Optional[float],
    rsi_above: Optional[float]
) -> bool:
    """
    檢查 RSI 是否滿足觸發條件.
    
    Args:
        current_rsi: 當前 RSI 值
        rsi_below: 超賣閾值 (RSI < this)
        rsi_above: 超買閾值 (RSI > this)
    
    Returns:
        滿足任何條件返回 True
    """
    if current_rsi is None:
        return False
    
    if rsi_below is not None and current_rsi < rsi_below:
        return True
    
    if rsi_above is not None and current_rsi > rsi_above:
        return True
    
    return False


def _evaluate_trigger_conditions(
    price_condition_met: bool,
    rsi_condition_met: bool,
    trigger_mode: str
) -> bool:
    """
    根據觸發模式評估複合條件.
    
    Args:
        price_condition_met: 價格條件是否滿足
        rsi_condition_met: RSI 條件是否滿足
        trigger_mode: 觸發模式 ("price", "rsi", "both" 或 "either")
    
    Returns:
        應該觸發警報返回 True
    """
    if trigger_mode == "price":
        # 只檢查價格條件
        return price_condition_met
    elif trigger_mode == "rsi":
        # 只檢查 RSI 條件
        return rsi_condition_met
    elif trigger_mode == "both":
        # 兩個條件都必須滿足（價格 AND RSI）
        return price_condition_met and rsi_condition_met
    elif trigger_mode == "either":
        # 任一條件滿足即觸發（價格 OR RSI）
        return price_condition_met or rsi_condition_met
    
    # 預設為價格模式
    return price_condition_met


async def check_prices():
    """Fetch all active tracked indices and send alerts if triggered (支持 RSI 複合條件)."""
    logger.info(f"[Scheduler] Running price check at {datetime.now(timezone.utc)}")
    sb = get_supabase()
    rsi_service = get_rsi_calculation_service()

    # Get all active tracked indices with user profiles
    # 包括 RSI 相關欄位
    indices_res = (
        sb.table("tracked_indices")
        .select("*, profiles(email, line_user_id, notify_email, notify_line)")
        .eq("is_active", True)
        .execute()
    )

    if not indices_res.data:
        logger.info("[Scheduler] No active tracked indices found.")
        return

    for item in indices_res.data:
        tracking_id = item["id"]
        symbol = item["symbol"]
        category = item["category"]
        trigger_mode = item.get("trigger_mode", "price")
        notify_channel = item.get("notify_channel", "email")
        alert_triggered = item.get("alert_triggered", False)
        profile = item.get("profiles", {}) or {}

        try:
            # 1. 更新當前價格
            current_price = await get_current_price(symbol, category)
            if current_price is None:
                logger.warning(f"[Scheduler] 無法獲取 {symbol} 的價格，跳過")
                continue

            sb.table("tracked_indices").update({
                "current_price": current_price,
                "price_updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", tracking_id).execute()

            # 2. 如果需要 RSI，計算並更新 RSI
            current_rsi = item.get("current_rsi")
            if trigger_mode in ("rsi", "both", "either"):
                rsi_period = item.get("rsi_period", 14)
                success = await rsi_service.update_rsi_for_tracked_index(
                    tracking_id, symbol, category, rsi_period
                )
                if success:
                    # 刷新 item 以獲得最新的 RSI 值
                    updated = sb.table("tracked_indices").select("current_rsi").eq("id", tracking_id).single().execute()
                    if updated.data:
                        current_rsi = updated.data.get("current_rsi")

            # 3. 檢查價格條件
            price_condition_met = False
            trigger_price = item.get("trigger_price")
            if trigger_price is not None:
                trigger_direction = item.get("trigger_direction", "above")
                price_condition_met = _check_price_condition(
                    current_price, float(trigger_price), trigger_direction
                )

            # 4. 檢查 RSI 條件
            rsi_condition_met = _check_rsi_condition(
                current_rsi,
                item.get("rsi_below"),
                item.get("rsi_above")
            )

            # 5. 評估複合條件
            condition_met = _evaluate_trigger_conditions(
                price_condition_met,
                rsi_condition_met,
                trigger_mode
            )

            # 6. 決定是否發送通知
            should_notify = False
            if condition_met and not alert_triggered:
                # 首次觸發
                should_notify = True
                logger.info(f"[Scheduler] ✓ 首次觸發: {symbol} (price={current_price}, rsi={current_rsi}, mode={trigger_mode})")
            elif condition_met and alert_triggered:
                # 條件仍滿足，檢查 24 小時冷卻時間
                last_notified = item.get("last_notified_at")
                if not last_notified:
                    should_notify = True
                else:
                    last_dt = datetime.fromisoformat(last_notified.replace("Z", "+00:00"))
                    elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
                    if elapsed >= 86400:  # 24 小時
                        should_notify = True
                        logger.info(f"[Scheduler] 每日提醒: {symbol}")
            elif not condition_met and alert_triggered:
                # 條件已不再滿足，重置觸發狀態，停止重複通知
                sb.table("tracked_indices").update({"alert_triggered": False}).eq("id", tracking_id).execute()
                logger.info(f"[Scheduler] ↺ 重置觸發狀態: {symbol} (price={current_price}, rsi={current_rsi}, mode={trigger_mode})")

            if not should_notify:
                continue

            # 7. 發送通知
            global_notify = profile.get("global_notify", True)
            send_email_flag = global_notify and notify_channel in ("email", "both") and profile.get("notify_email")
            send_line_flag = global_notify and notify_channel in ("line", "both") and profile.get("notify_line")

            email = profile.get("email")
            line_user_id = profile.get("line_user_id")

            if not send_email_flag and not send_line_flag:
                logger.warning(
                    f"[Scheduler] ⚠ {symbol} 條件已觸發但無可用通知管道 "
                    f"(notify_channel={notify_channel}, notify_email={profile.get('notify_email')}, "
                    f"notify_line={profile.get('notify_line')}, line_user_id={'有' if line_user_id else '無'})"
                )

            success = False
            channel_used = []

            if send_email_flag and email:
                subject, body = build_alert_email(
                    symbol=symbol,
                    name=item["name"],
                    category=category,
                    current_price=current_price,
                    trigger_price=float(trigger_price) if trigger_price is not None else current_price,
                    trigger_direction=item.get("trigger_direction", "above"),
                    tracking_id=tracking_id,
                    trigger_mode=trigger_mode,
                    current_rsi=current_rsi,
                    rsi_below=item.get("rsi_below"),
                    rsi_above=item.get("rsi_above"),
                    price_condition_met=price_condition_met,
                    rsi_condition_met=rsi_condition_met,
                )
                ok = await send_email(email, subject, body)
                if ok:
                    success = True
                    channel_used.append("email")

            if send_line_flag and line_user_id:
                msg = build_alert_message(
                    symbol=symbol,
                    name=item["name"],
                    current_price=current_price,
                    trigger_price=float(trigger_price) if trigger_price is not None else current_price,
                    trigger_direction=item.get("trigger_direction", "above"),
                    tracking_id=tracking_id,
                    trigger_mode=trigger_mode,
                    current_rsi=current_rsi,
                    rsi_below=item.get("rsi_below"),
                    rsi_above=item.get("rsi_above"),
                    price_condition_met=price_condition_met,
                    rsi_condition_met=rsi_condition_met,
                )
                res = await send_line_message(line_user_id, msg)
                if res.get("success"):
                    success = True
                    channel_used.append("line")

            # 8. 更新通知時間戳，並在首次成功後才標記 alert_triggered
            if success:
                update_fields = {"last_notified_at": datetime.now(timezone.utc).isoformat()}
                if not alert_triggered:
                    update_fields["alert_triggered"] = True
                try:
                    sb.table("tracked_indices").update(update_fields).eq("id", tracking_id).execute()
                except Exception as upd_err:
                    logger.error(f"[Scheduler] Failed to update tracked_indices for {symbol}: {upd_err}")

            # 9. 記錄警報日誌（獨立 try/except，不阻斷流程）
            try:
                sb.table("alert_logs").insert({
                    "user_id": item["user_id"],
                    "tracked_index_id": tracking_id,
                    "symbol": symbol,
                    "trigger_price": item.get("trigger_price"),
                    "current_price": current_price,
                    "current_rsi": current_rsi,
                    "trigger_mode": trigger_mode,
                    "channel": ",".join(channel_used) if channel_used else notify_channel,
                    "status": "sent" if success else "failed",
                }).execute()
            except Exception as log_err:
                logger.error(f"[Scheduler] Failed to save alert_log for {symbol}: {log_err}")

        except Exception as e:
            logger.error(f"[Scheduler] Error processing {symbol}: {e}")

    logger.info("[Scheduler] Price check complete.")



async def run_tw_etf_sync():
    """Wrapper to run sync_tw_etf_list and log outcome."""
    try:
        count = await sync_tw_etf_list()
        logger.info(f"[Scheduler] TW ETF sync complete: {count} records updated.")
    except Exception as e:
        logger.error(f"[Scheduler] TW ETF sync failed: {e}")


async def run_us_etf_sync():
    """Wrapper to run sync_us_etf_list and log outcome."""
    try:
        count = await sync_us_etf_list()
        logger.info(f"[Scheduler] US ETF sync complete: {count} records updated.")
    except Exception as e:
        logger.error(f"[Scheduler] US ETF sync failed: {e}")


async def run_briefing_job():
    """Wrapper to run market briefing session and log outcome."""
    try:
        stats = await run_market_briefing_session()
        logger.info(f"[Scheduler] Briefing job complete: {stats}")
    except Exception as e:
        logger.error(f"[Scheduler] Briefing job failed: {e}")


async def run_dividend_sync():
    """Wrapper to run dividend calendar sync and log outcome."""
    try:
        count = await sync_dividend_calendar()
        logger.info(f"[Scheduler] Dividend sync complete: {count} records updated.")
    except Exception as e:
        logger.error(f"[Scheduler] Dividend sync failed: {e}")


async def run_dividend_notify_check():
    """Wrapper to check and send dividend reminders to tracked-stock owners."""
    try:
        stats = await check_and_send_dividend_notifications()
        logger.info(f"[Scheduler] Dividend notify complete: {stats}")
    except Exception as e:
        logger.error(f"[Scheduler] Dividend notify failed: {e}")


def start_scheduler():
    scheduler.add_job(check_prices, "interval", minutes=30, id="price_check", replace_existing=True)
    # Sync TW ETF list daily at 01:00 Asia/Taipei
    scheduler.add_job(run_tw_etf_sync, "cron", hour=1, minute=0, id="tw_etf_sync", replace_existing=True)
    # Sync US ETF list daily at 02:00 Asia/Taipei
    scheduler.add_job(run_us_etf_sync, "cron", hour=2, minute=0, id="us_etf_sync", replace_existing=True)
    # AI Market Briefing: 08:00, 13:00, 18:00 Asia/Taipei
    scheduler.add_job(run_briefing_job, "cron", hour=8, minute=0, id="briefing_0800", replace_existing=True)
    scheduler.add_job(run_briefing_job, "cron", hour=13, minute=0, id="briefing_1300", replace_existing=True)
    scheduler.add_job(run_briefing_job, "cron", hour=18, minute=0, id="briefing_1800", replace_existing=True)
    # Dividend calendar sync at 06:00 Asia/Taipei
    scheduler.add_job(run_dividend_sync, "cron", hour=6, minute=0, id="dividend_sync", replace_existing=True)
    # Dividend notification check at 06:30 (after sync completes)
    scheduler.add_job(run_dividend_notify_check, "cron", hour=6, minute=30, id="dividend_notify", replace_existing=True)
    scheduler.start()
    logger.info(
        "[Scheduler] Started: price_check (every 30 min), tw_etf_sync (daily 01:00), "
        "us_etf_sync (daily 02:00), briefing (08:00/13:00/18:00), "
        "dividend_sync (06:00), dividend_notify (06:30)"
    )
