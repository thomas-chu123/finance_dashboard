"""
Price monitoring scheduler.
Runs every 30 minutes to check tracked indices and send alerts.
Also syncs TW ETF list from TWSE daily at 01:00 Asia/Taipei.
"""
import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import get_supabase
from app.services.market_data import get_current_price
from app.services.email_service import send_email, build_alert_email
from app.services.line_service import send_line_message, build_alert_message
from app.services.tw_etf_sync import sync_tw_etf_list
from app.services.us_etf_sync import sync_us_etf_list

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Taipei")


async def check_prices():
    """Fetch all active tracked indices and send alerts if triggered."""
    logger.info(f"[Scheduler] Running price check at {datetime.now(timezone.utc)}")
    sb = get_supabase()

    # Get all active tracked indices with user profiles
    indices_res = (
        sb.table("tracked_indices")
        .select("*, profiles(email, line_user_id, notify_email, notify_line)")
        .eq("is_active", True)
        .not_.is_("trigger_price", "null")
        .execute()
    )

    if not indices_res.data:
        logger.info("[Scheduler] No active tracked indices with triggers found.")
        return

    for item in indices_res.data:
        tracking_id = item["id"]
        symbol = item["symbol"]
        category = item["category"]
        trigger_price = float(item["trigger_price"])
        trigger_direction = item["trigger_direction"]
        notify_channel = item["notify_channel"]
        alert_triggered = item.get("alert_triggered", False)
        profile = item.get("profiles", {}) or {}

        try:
            current_price = await get_current_price(symbol, category)
            if current_price is None:
                continue

            # Update current price in DB
            sb.table("tracked_indices").update({
                "current_price": current_price,
                "price_updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", tracking_id).execute()

            # Check trigger condition
            condition_met = False
            if trigger_direction == "above" and current_price >= trigger_price:
                condition_met = True
            elif trigger_direction == "below" and current_price <= trigger_price:
                condition_met = True

            # Logic for "Daily Notify" once triggered:
            # 1. If not yet triggered but condition met -> Trigger it and Notify.
            # 2. If already triggered -> Notify every 24 hours regardless of current price? 
            #    Actually, usually it should stay 'triggered' until user stops it.
            #    User said: "希望是每天送notify, 但在email及line上可以按停止通知"
            
            should_notify = False
            if condition_met and not alert_triggered:
                # First time trigger
                should_notify = True
                sb.table("tracked_indices").update({"alert_triggered": True}).eq("id", tracking_id).execute()
                logger.info(f"[Scheduler] TRIGERRED: {symbol} hit {current_price}")
            elif alert_triggered:
                # Already triggered, check for daily reminder (24h cooldown)
                last_notified = item.get("last_notified_at")
                if not last_notified:
                    should_notify = True
                else:
                    last_dt = datetime.fromisoformat(last_notified.replace("Z", "+00:00"))
                    elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
                    if elapsed >= 86400:  # 24 hours
                        should_notify = True

            if not should_notify:
                continue

            logger.info(f"[Scheduler] ALERT: {symbol} @ {current_price} (Daily reminder or first trigger)")

            # Determine channels
            send_email_flag = notify_channel in ("email", "both") and profile.get("notify_email")
            send_line_flag = notify_channel in ("line", "both") and profile.get("notify_line")
            email = profile.get("email")
            line_user_id = profile.get("line_user_id")

            success = False
            channel_used = []

            if send_email_flag and email:
                subject, body = build_alert_email(
                    symbol=symbol,
                    name=item["name"],
                    category=category,
                    current_price=current_price,
                    trigger_price=trigger_price,
                    trigger_direction=trigger_direction,
                    tracking_id=tracking_id,
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
                    trigger_price=trigger_price,
                    trigger_direction=trigger_direction,
                    tracking_id=tracking_id,
                )
                res = await send_line_message(line_user_id, msg)
                if res.get("success"):
                    success = True
                    channel_used.append("line")

            # Update last_notified_at
            if success:
                sb.table("tracked_indices").update({
                    "last_notified_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", tracking_id).execute()

            # Log the alert
            sb.table("alert_logs").insert({
                "user_id": item["user_id"],
                "tracked_index_id": tracking_id,
                "symbol": symbol,
                "trigger_price": trigger_price,
                "current_price": current_price,
                "channel": ",".join(channel_used) if channel_used else notify_channel,
                "status": "sent" if success else "failed",
            }).execute()

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


def start_scheduler():
    scheduler.add_job(check_prices, "interval", minutes=30, id="price_check", replace_existing=True)
    # Sync TW ETF list daily at 01:00 Asia/Taipei
    scheduler.add_job(run_tw_etf_sync, "cron", hour=1, minute=0, id="tw_etf_sync", replace_existing=True)
    # Sync US ETF list daily at 02:00 Asia/Taipei
    scheduler.add_job(run_us_etf_sync, "cron", hour=2, minute=0, id="us_etf_sync", replace_existing=True)
    scheduler.start()
    logger.info("[Scheduler] Started: price_check (every 30 min), tw_etf_sync (daily 01:00), us_etf_sync (daily 02:00)")
