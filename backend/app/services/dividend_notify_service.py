"""
Dividend Notification Service
Sends ex-dividend/ex-right reminders to users who actively track the stock.
Notification eligibility is derived from tracked_indices (no separate subscription table).
"""
import logging
from datetime import date, timedelta, datetime, timezone
from app.database import get_supabase
from app.services.email_service import send_email
from app.services.line_service import send_line_message

logger = logging.getLogger(__name__)


def _normalize_code(symbol: str) -> str:
    """Strip exchange suffix from a symbol.

    Examples: '2330.TW' -> '2330', '0050.TWO' -> '0050'
    """
    return symbol.split(".")[0]


def _build_dividend_email(
    symbol: str,
    name: str,
    ex_date: str,
    ex_type: str,
    cash_dividend: float | None,
    days_before: int,
    app_url: str,
) -> tuple[str, str]:
    """Build dividend reminder email (subject, HTML body)."""
    type_label = "除息" if ex_type == "息" else "除權" if ex_type == "權" else "除權息"
    days_label = f"{days_before} 天後"
    dividend_str = f"${cash_dividend:.4f} 元/股" if cash_dividend else "詳見公告"
    subject = f"【{type_label}提醒 - {days_label}】{symbol} {name}"

    body = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="utf-8"><title>{subject}</title></head>
<body style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;background:#f9fbfb;margin:0;padding:0;color:#333;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f9fbfb;">
    <tr>
      <td align="center" style="padding:20px 16px 40px;">
        <table width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,0.05);">
          <tr>
            <td style="background:linear-gradient(135deg,#10b981,#047857);padding:30px 20px;text-align:center;">
              <h1 style="margin:0;color:white;font-size:20px;letter-spacing:1px;">NEXUS. FINANCE</h1>
              <div style="display:inline-block;background:rgba(255,255,255,0.2);color:white;padding:4px 12px;border-radius:20px;font-size:12px;margin-top:10px;font-weight:bold;">{type_label}提醒：{days_label}</div>
            </td>
          </tr>
          <tr>
            <td style="padding:30px;">
              <p style="font-size:15px;color:#555;margin:0 0 20px;">您追蹤的投資標的即將{type_label}：</p>
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="background:#f8fcf9;border-radius:8px;border-left:4px solid #10b981;">
                <tr>
                  <td style="padding:20px;">
                    <div style="font-size:24px;font-weight:800;color:#047857;margin-bottom:5px;">{symbol} <span style="font-size:16px;font-weight:400;color:#666;">({name})</span></div>
                    <div style="color:#7f8c8d;font-size:14px;margin-bottom:15px;">{type_label}日：{ex_date}（還有 {days_before} 天）</div>
                    <div style="font-size:14px;color:#374151;background:#ecfdf5;padding:10px;border-radius:4px;">
                      {'現金股利：' + dividend_str if ex_type in ('息', '權息') else '股票股利詳見公告'}
                    </div>
                  </td>
                </tr>
              </table>
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:30px;">
                <tr>
                  <td align="center">
                    <a href="{app_url}/dividend-calendar"
                       style="display:inline-block;background:#10b981;color:white;padding:12px 35px;text-decoration:none;border-radius:6px;font-weight:bold;font-size:14px;">
                      查看除息日曆
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="background:#f9fbfb;padding:20px;text-align:center;font-size:12px;color:#95a5a6;border-top:1px solid #e5e7eb;">
              這是一封自動發出的通知信，請勿直接回覆。<br>
              © 2026 Nexus Finance Dashboard. All rights reserved.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return subject, body


def _build_dividend_line_msg(
    symbol: str,
    name: str,
    ex_date: str,
    ex_type: str,
    cash_dividend: float | None,
    days_before: int,
) -> str:
    """Build LINE message for dividend reminder."""
    type_label = "除息" if ex_type == "息" else "除權" if ex_type == "權" else "除權息"
    dividend_str = f"${cash_dividend:.4f} 元/股" if cash_dividend else "詳見公告"
    return (
        f"【{type_label}提醒 - {days_before} 天後】\n"
        f"📌 {symbol} {name}\n"
        f"{type_label}日：{ex_date}\n"
        f"{'現金股利：' + dividend_str if ex_type in ('息', '權息') else '股票股利詳見公告'}\n\n"
        f"請提前確認持股！\n"
        f"登入 Finance Dashboard 查看除息日曆。"
    )


async def check_and_send_dividend_notifications() -> dict:
    """Check upcoming dividend dates and notify users who actively track those stocks.

    Checks ex-dates at today+7 (trigger_mode='dividend_7d') and
    today+1 (trigger_mode='dividend_1d').

    Returns:
        {"checked": int, "sent": int, "skipped": int, "failed": int}
    """
    from app.config import get_settings
    settings = get_settings()
    app_url = getattr(settings, "app_base_url", "")
    today = date.today()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc).isoformat()

    targets = [
        (today + timedelta(days=7), "dividend_7d", 7),
        (today + timedelta(days=1), "dividend_1d", 1),
    ]

    sb = get_supabase()
    stats = {"checked": 0, "sent": 0, "skipped": 0, "failed": 0}

    for target_date, trigger_mode, days_before in targets:
        target_date_str = target_date.isoformat()

        # 1. Get all dividend records for the target date
        try:
            div_res = (
                sb.table("dividend_calendar")
                .select("code, name, ex_date, ex_type, cash_dividend")
                .eq("ex_date", target_date_str)
                .execute()
            )
        except Exception as e:
            logger.error(f"[DividendNotify] Failed to query dividend_calendar for {target_date_str}: {e}")
            continue

        dividend_items = div_res.data or []
        if not dividend_items:
            logger.info(f"[DividendNotify] No dividends on {target_date_str}")
            continue

        logger.info(f"[DividendNotify] {len(dividend_items)} dividend(s) on {target_date_str}")

        # 2. Fetch all active tracked_indices once (to avoid N+1 queries)
        try:
            track_res = (
                sb.table("tracked_indices")
                .select("id, user_id, symbol, notify_channel, profiles(email, line_user_id, notify_email, notify_line, global_notify)")
                .eq("is_active", True)
                .execute()
            )
        except Exception as e:
            logger.error(f"[DividendNotify] Failed to query tracked_indices: {e}")
            continue

        all_tracking = track_res.data or []

        for div in dividend_items:
            code = div["code"]
            name = div["name"]
            ex_date = div["ex_date"]
            ex_type = div["ex_type"]
            cash_dividend = div.get("cash_dividend")

            # 3. Filter trackers whose base code matches
            matching = [t for t in all_tracking if _normalize_code(t["symbol"]) == code]
            if not matching:
                continue

            for tracked in matching:
                stats["checked"] += 1
                tracking_id = tracked["id"]
                user_id = tracked["user_id"]
                notify_channel = tracked.get("notify_channel", "email")
                profile = tracked.get("profiles") or {}

                if not profile.get("global_notify", True):
                    stats["skipped"] += 1
                    continue

                # 4. Duplicate protection: skip if already notified today
                try:
                    dup_res = (
                        sb.table("alert_logs")
                        .select("id")
                        .eq("user_id", user_id)
                        .eq("symbol", code)
                        .eq("trigger_mode", trigger_mode)
                        .gte("created_at", today_start)
                        .limit(1)
                        .execute()
                    )
                    if dup_res.data:
                        logger.info(f"[DividendNotify] Already notified {user_id} for {code} ({trigger_mode}), skip.")
                        stats["skipped"] += 1
                        continue
                except Exception as e:
                    logger.warning(f"[DividendNotify] Duplicate check failed for {user_id}/{code}: {e}")

                # 5. Determine send flags
                send_email_flag = (
                    notify_channel in ("email", "both")
                    and profile.get("notify_email")
                    and profile.get("email")
                )
                send_line_flag = (
                    notify_channel in ("line", "both")
                    and profile.get("notify_line")
                    and profile.get("line_user_id")
                )

                if not send_email_flag and not send_line_flag:
                    logger.warning(f"[DividendNotify] No active channel for user {user_id} / {code}")
                    stats["skipped"] += 1
                    continue

                success = False
                channel_used = []

                if send_email_flag:
                    try:
                        subject, body = _build_dividend_email(
                            symbol=code, name=name, ex_date=ex_date,
                            ex_type=ex_type, cash_dividend=cash_dividend,
                            days_before=days_before, app_url=app_url,
                        )
                        ok = await send_email(profile["email"], subject, body)
                        if ok:
                            success = True
                            channel_used.append("email")
                    except Exception as e:
                        logger.error(f"[DividendNotify] Email failed for {user_id}/{code}: {e}")

                if send_line_flag:
                    try:
                        msg = _build_dividend_line_msg(
                            symbol=code, name=name, ex_date=ex_date,
                            ex_type=ex_type, cash_dividend=cash_dividend,
                            days_before=days_before,
                        )
                        res = await send_line_message(profile["line_user_id"], msg)
                        if res.get("success"):
                            success = True
                            channel_used.append("line")
                    except Exception as e:
                        logger.error(f"[DividendNotify] LINE failed for {user_id}/{code}: {e}")

                if success:
                    stats["sent"] += 1
                    # 6. Record to alert_logs
                    try:
                        sb.table("alert_logs").insert({
                            "user_id": user_id,
                            "tracked_index_id": tracking_id,
                            "symbol": code,
                            "trigger_price": None,
                            "current_price": None,
                            "trigger_mode": trigger_mode,
                            "channel": ",".join(channel_used),
                            "status": "sent",
                        }).execute()
                    except Exception as log_err:
                        logger.error(f"[DividendNotify] Failed to write alert_log: {log_err}")
                else:
                    stats["failed"] += 1

    logger.info(f"[DividendNotify] Complete: {stats}")
    return stats
