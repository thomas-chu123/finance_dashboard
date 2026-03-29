"""Email notification service (adapted from medical project)."""
import traceback
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import get_settings

settings = get_settings()


async def send_email(to_email: str, subject: str, body_html: str) -> bool:
    if not settings.smtp_user or not settings.smtp_password:
        print("[Email] SMTP credentials not configured, skipping.")
        return False

    # --- SMTP debug: 印出當前設定（密碼僅顯示前3字元）---
    pwd_hint = (settings.smtp_password[:3] + "***") if settings.smtp_password else "(empty)"

    # Zoho(及多數 SMTP server) 要求 From 地址必須與認證帳號一致，否則回傳
    # "Sender is not allowed to relay emails"。若 smtp_from 未設定，自動 fallback。
    from_addr = settings.smtp_from if settings.smtp_from else settings.smtp_user
    if from_addr != settings.smtp_user:
        print(
            f"[Email][SMTP-DEBUG] ⚠️  WARNING: smtp_from={from_addr!r} != smtp_user={settings.smtp_user!r}. "
            f"Zoho will reject this with 'Sender is not allowed to relay emails'. "
            f"Set SMTP_FROM to the same address as SMTP_USER in .env."
        )

    print(
        f"[Email][SMTP-DEBUG] Config: "
        f"host={settings.smtp_host!r}, port={settings.smtp_port}, "
        f"user={settings.smtp_user!r}, from={from_addr!r}, "
        f"password_hint={pwd_hint}, start_tls=True"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{from_addr}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    print(f"[Email][SMTP-DEBUG] Attempting to connect to {settings.smtp_host}:{settings.smtp_port} ...")
    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        print(f"[Email][SMTP-DEBUG] Connection & AUTH succeeded.")
        print(f"[Email] Sent to {to_email}: {subject}")
        return True
    except aiosmtplib.SMTPAuthenticationError as e:
        print(f"[Email][SMTP-DEBUG] AUTH FAILED (check user/password): {e}")
        return False
    except aiosmtplib.SMTPConnectError as e:
        print(f"[Email][SMTP-DEBUG] CONNECT FAILED (check host/port/firewall): {e}")
        return False
    except aiosmtplib.SMTPException as e:
        print(f"[Email][SMTP-DEBUG] SMTP error: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        return False
    except Exception as e:
        print(f"[Email] Failed to send to {to_email}: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        return False


def _fmt_threshold(v: float) -> str:
    """格式化閾值，整數顯示無小數點，浮點數保留必要小數（不取整）。"""
    return f"{v:g}"


def _build_rsi_condition_label(
    current_rsi: float | None,
    rsi_below: float | None,
    rsi_above: float | None,
) -> str:
    """根據當前 RSI 值與閾值，產生精確的 RSI 觸發條件描述。"""
    if rsi_below is not None and rsi_above is not None:
        if current_rsi is not None and current_rsi < rsi_below:
            return f"RSI 閥值跌破 {_fmt_threshold(rsi_below)}"
        if current_rsi is not None and current_rsi > rsi_above:
            return f"RSI 閥值突破 {_fmt_threshold(rsi_above)}"
        return f"RSI 閥值跌破 {_fmt_threshold(rsi_below)} 或突破 {_fmt_threshold(rsi_above)}"
    if rsi_below is not None:
        return f"RSI 閥值跌破 {_fmt_threshold(rsi_below)}"
    if rsi_above is not None:
        return f"RSI 閥值突破 {_fmt_threshold(rsi_above)}"
    return "RSI 觸發"


def _build_trigger_condition_label(
    trigger_direction: str,
    trigger_price: float | None,
    trigger_mode: str,
    current_rsi: float | None,
    rsi_below: float | None,
    rsi_above: float | None,
    price_condition_met: bool = True,
    rsi_condition_met: bool = True,
) -> str:
    """產生觸發條件描述，依實際觸發情況顯示（either 模式只顯示實際觸發的條件）。"""
    price_dir = "突破" if trigger_direction == "above" else "跌破"
    price_label = f"價格{price_dir} {trigger_price:.2f}" if trigger_price is not None else ""
    rsi_label = _build_rsi_condition_label(current_rsi, rsi_below, rsi_above)

    if trigger_mode == "price":
        return price_label
    if trigger_mode == "rsi":
        return rsi_label
    if trigger_mode == "both":
        # "both" 模式：只顯示實際已觸發的條件（防禦性寫法）
        parts = []
        if price_condition_met and price_label:
            parts.append(price_label)
        if rsi_condition_met and rsi_label:
            parts.append(rsi_label)
        return " 及 ".join(parts) if parts else (price_label or rsi_label)
    if trigger_mode == "either":
        # 只顯示實際觸發的條件，不顯示未觸發的條件
        if price_condition_met and rsi_condition_met:
            parts = [p for p in (price_label, rsi_label) if p]
            return " 及 ".join(parts) if parts else price_label
        elif price_condition_met:
            return price_label
        elif rsi_condition_met:
            return rsi_label
    return price_label


def _build_actual_mode_desc(
    trigger_mode: str,
    price_condition_met: bool,
    rsi_condition_met: bool,
) -> str:
    """依實際觸發情況產生模式描述文字。"""
    if trigger_mode == "either":
        if price_condition_met and rsi_condition_met:
            return "價格及 RSI"
        elif price_condition_met:
            return "價格"
        else:
            return "RSI 指標"
    return {
        "price": "價格",
        "rsi": "RSI 指標",
        "both": "價格及 RSI",
        "either": "價格或 RSI",
    }.get(trigger_mode, "價格")


def build_alert_email(
    symbol: str,
    name: str,
    category: str,
    current_price: float,
    trigger_price: float,
    trigger_direction: str,
    tracking_id: str,
    trigger_mode: str = "price",
    current_rsi: float | None = None,
    rsi_below: float | None = None,
    rsi_above: float | None = None,
    price_condition_met: bool = True,
    rsi_condition_met: bool = True,
) -> tuple[str, str]:
    mode_desc = _build_actual_mode_desc(trigger_mode, price_condition_met, rsi_condition_met)

    trigger_condition = _build_trigger_condition_label(
        trigger_direction, trigger_price, trigger_mode,
        current_rsi, rsi_below, rsi_above,
        price_condition_met, rsi_condition_met,
    )

    # 依實際觸發情況產生 Email 標題
    price_dir = "突破" if trigger_direction == "above" else "跌破"
    if trigger_mode == "price":
        subject = f"📊 投資提醒：{name} ({symbol}) 價格已{price_dir} {trigger_price:.2f}"
    elif trigger_mode == "rsi":
        rsi_desc = _build_rsi_condition_label(current_rsi, rsi_below, rsi_above)
        subject = f"📊 投資提醒：{name} ({symbol}) {rsi_desc}"
    elif trigger_mode == "both":
        subject = f"📊 投資提醒：{name} ({symbol}) 價格及 RSI 均已觸發"
    elif trigger_mode == "either":
        if price_condition_met and not rsi_condition_met:
            subject = f"📊 投資提醒：{name} ({symbol}) 價格已{price_dir} {trigger_price:.2f}"
        elif rsi_condition_met and not price_condition_met:
            rsi_desc = _build_rsi_condition_label(current_rsi, rsi_below, rsi_above)
            subject = f"📊 投資提醒：{name} ({symbol}) {rsi_desc}"
        else:
            subject = f"📊 投資提醒：{name} ({symbol}) 價格及 RSI 均已觸發"
    else:
        subject = f"📊 投資提醒：{name} ({symbol}) 價格已{price_dir} {trigger_price:.2f}"

    # 依實際觸發條件決定強調色：跌破/超賣用紅，突破/超買用綠，RSI 正常範圍用藍
    is_bearish = (price_condition_met and trigger_direction == "below") or (
        rsi_condition_met and rsi_below is not None and current_rsi is not None and current_rsi < rsi_below
    )
    is_bullish = (price_condition_met and trigger_direction == "above") or (
        rsi_condition_met and rsi_above is not None and current_rsi is not None and current_rsi > rsi_above
    )
    accent = "#e74c3c" if is_bearish else "#10b981" if is_bullish else "#3b82f6"
    price_accent = "#e74c3c" if trigger_direction == "below" else "#10b981"
    alert_bgc = "#fdf2f2" if is_bearish else "#f0fdf4" if is_bullish else "#eff6ff"
    status_badge_bg = "#e74c3c" if is_bearish else "#22c55e" if is_bullish else "#3b82f6"

    # RSI 欄位（顯示於目前價格右側）
    rsi_col_html = "<td></td>"
    if current_rsi is not None:
        if rsi_below is not None and current_rsi < rsi_below:
            rsi_disp_color = "#e74c3c"
            rsi_status_badge = '<span style="font-size:12px;background:#fee2e2;padding:2px 6px;border-radius:4px;margin-left:4px;">超賣</span>'
        elif rsi_above is not None and current_rsi > rsi_above:
            rsi_disp_color = "#10b981"
            rsi_status_badge = '<span style="font-size:12px;background:#dcfce7;padding:2px 6px;border-radius:4px;margin-left:4px;">超買</span>'
        else:
            rsi_disp_color = "#3b82f6"
            rsi_status_badge = ""
        rsi_col_html = f'<td style="width:50%;vertical-align:top;"><div style="font-size:12px;color:#7f8c8d;margin-bottom:5px;">目前 RSI</div><div style="font-size:28px;font-weight:bold;color:{rsi_disp_color};">{current_rsi:.2f} {rsi_status_badge}</div></td>'

    body = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;background-color:#f9fbfb;margin:0;padding:0;color:#333;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f9fbfb;">
    <tr>
      <td align="center" style="padding:20px 16px 40px;">

        <!-- Outer card -->
        <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,0.05);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#10b981,#047857);padding:30px 20px;text-align:center;">
              <h1 style="margin:0;color:white;font-size:20px;letter-spacing:1px;">NEXUS. FINANCE</h1>
              <div style="display:inline-block;background:{status_badge_bg};color:white;padding:4px 12px;border-radius:20px;font-size:12px;margin-top:10px;font-weight:bold;">觸發提醒：{mode_desc}</div>
            </td>
          </tr>

          <!-- Content -->
          <tr>
            <td style="padding:30px;">
              <p style="font-size:15px;color:#555;margin:0 0 20px;">您追蹤的投資標的已達到預設的觸發條件：</p>

              <!-- Info card -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f8fcf9;border-radius:8px;border-left:4px solid #10b981;">
                <tr>
                  <td style="padding:20px;">
                    <div style="font-size:24px;font-weight:800;color:#047857;margin-bottom:5px;">{symbol} <span style="font-size:16px;font-weight:400;color:#666;">({name})</span></div>
                    <div style="color:#7f8c8d;font-size:14px;margin-bottom:15px;">資產類型：{category.upper()}</div>
                    <div style="color:{accent};font-weight:bold;font-size:14px;background:{alert_bgc};padding:10px;border-radius:4px;text-align:center;">
                      觸發條件：{trigger_condition}
                    </div>
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:20px;">
                      <tr>
                        <td style="width:50%;padding-right:10px;vertical-align:top;">
                          <div style="font-size:12px;color:#7f8c8d;margin-bottom:5px;">目前價格</div>
                          <div style="font-size:28px;font-weight:bold;color:{price_accent};">{current_price:.2f}</div>
                        </td>
                        {rsi_col_html}
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- CTA Button -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:30px;">
                <tr>
                  <td align="center">
                    <a href="{settings.app_base_url}/tracking"
                       style="display:inline-block;background-color:#10b981;color:white;padding:12px 35px;text-decoration:none;border-radius:6px;font-weight:bold;font-size:14px;">立即查看圖表</a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f9fbfb;padding:20px;text-align:center;font-size:12px;color:#95a5a6;border-top:1px solid #e5e7eb;">
              這是一封自動發出的通知信，請勿直接回覆。<br><br>
              想要停止此項目的通知？
              <a href="{settings.backend_base_url}/api/public/stop-notification/{tracking_id}"
                 style="color:#ef4444;text-decoration:none;font-weight:500;">點此停止通知</a><br><br>
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

