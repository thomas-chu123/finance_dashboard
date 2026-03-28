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
    accent = "#ef4444" if is_bearish else "#22c55e" if is_bullish else "#3b82f6"
    price_accent = "#ef4444" if trigger_direction == "below" else "#22c55e"

    # RSI 行（可選）
    rsi_row_html = ""
    if current_rsi is not None:
        if rsi_below is not None and current_rsi < rsi_below:
            rsi_color = "#ef4444"
            rsi_badge = f'<span style="display:inline-block;background:#450a0a;color:#fca5a5;padding:2px 8px;border-radius:20px;font-size:11px;margin-left:6px;">超賣</span>'
        elif rsi_above is not None and current_rsi > rsi_above:
            rsi_color = "#22c55e"
            rsi_badge = f'<span style="display:inline-block;background:#052e16;color:#86efac;padding:2px 8px;border-radius:20px;font-size:11px;margin-left:6px;">超買</span>'
        else:
            rsi_color = "#60a5fa"
            rsi_badge = ""
        rsi_row_html = f"""
          <tr>
            <td style="padding:14px 20px;color:#71717a;font-size:13px;border-top:1px solid #27272a;width:40%;">RSI (14)</td>
            <td style="padding:14px 20px;text-align:right;border-top:1px solid #27272a;">
              <span style="color:{rsi_color};font-size:22px;font-weight:700;letter-spacing:-0.5px;">{current_rsi:.2f}</span>{rsi_badge}
            </td>
          </tr>
        """

    favicon_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 48 48" fill="none">
      <circle cx="24" cy="24" r="22" fill="#52C279" opacity="0.95"/>
      <circle cx="24" cy="24" r="22" fill="url(#ng)" opacity="0.1"/>
      <circle cx="24" cy="24" r="18" fill="none" stroke="white" stroke-width="1.5" opacity="0.8"/>
      <path d="M 24 6 Q 25 15 24 24 Q 25 33 24 42" fill="none" stroke="white" stroke-width="1.2" opacity="0.7"/>
      <ellipse cx="24" cy="24" rx="17" ry="6" fill="none" stroke="white" stroke-width="1.2" opacity="0.7"/>
      <ellipse cx="24" cy="15" rx="16" ry="4" fill="none" stroke="white" stroke-width="0.8" opacity="0.5"/>
      <ellipse cx="24" cy="33" rx="16" ry="4" fill="none" stroke="white" stroke-width="0.8" opacity="0.5"/>
      <path d="M 32 18 Q 35 22 33 28 Q 30 32 24 33 L 24 18 Z" fill="white" opacity="0.15"/>
      <path d="M 18 22 Q 12 20 10 26 Q 12 32 18 30 Z" fill="white" opacity="0.1"/>
      <defs>
        <linearGradient id="ng" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#52C279;stop-opacity:1"/>
          <stop offset="100%" style="stop-color:#3DA35D;stop-opacity:1"/>
        </linearGradient>
      </defs>
    </svg>"""

    body = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background-color:#0c0c0e;font-family:'Inter','Helvetica Neue',Arial,sans-serif;-webkit-font-smoothing:antialiased;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#0c0c0e;min-height:100vh;">
    <tr>
      <td align="center" style="padding:32px 16px 48px;">

        <!-- Outer card -->
        <table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;background:#111113;border:1px solid #27272a;border-radius:20px;overflow:hidden;box-shadow:0 24px 64px rgba(0,0,0,0.7);">

          <!-- Top green accent bar -->
          <tr>
            <td style="height:3px;background:linear-gradient(90deg,#15803d 0%,#22c55e 50%,#15803d 100%);padding:0;line-height:0;font-size:0;">&nbsp;</td>
          </tr>

          <!-- Header -->
          <tr>
            <td align="center" style="padding:36px 32px 32px;background:linear-gradient(160deg,#0d2818 0%,#111113 65%);">

              <!-- SVG Logo -->
              <div style="margin-bottom:14px;">
                {favicon_svg}
              </div>

              <!-- Brand name -->
              <div style="margin-bottom:18px;line-height:1;">
                <span style="color:#22c55e;font-size:18px;font-weight:700;letter-spacing:0.3px;">NEXUS.</span>
                <span style="color:#52525b;font-size:13px;font-weight:400;margin-left:6px;">Finance Dashboard</span>
              </div>

              <!-- Divider -->
              <div style="width:48px;height:2px;background:linear-gradient(90deg,transparent,#22c55e,transparent);margin:0 auto 20px;"></div>

              <!-- Title -->
              <h1 style="color:#fafafa;margin:0;font-size:20px;font-weight:600;letter-spacing:-0.3px;">{mode_desc}觸發通知</h1>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:28px 32px 8px;">
              <p style="color:#71717a;font-size:13px;margin:0 0 20px;line-height:1.6;">您追蹤的指數已達到您設定的觸發條件：</p>

              <!-- Info table card -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#18181b;border:1px solid #27272a;border-radius:14px;overflow:hidden;">
                <tr>
                  <td style="padding:13px 20px;color:#71717a;font-size:13px;width:40%;border-bottom:1px solid #27272a;">代碼</td>
                  <td style="padding:13px 20px;color:#fafafa;font-size:14px;font-weight:600;text-align:right;border-bottom:1px solid #27272a;">{symbol}</td>
                </tr>
                <tr>
                  <td style="padding:13px 20px;color:#71717a;font-size:13px;border-bottom:1px solid #27272a;">名稱</td>
                  <td style="padding:13px 20px;color:#fafafa;font-size:14px;font-weight:600;text-align:right;border-bottom:1px solid #27272a;">{name}</td>
                </tr>
                <tr>
                  <td style="padding:13px 20px;color:#71717a;font-size:13px;border-bottom:1px solid #27272a;">類別</td>
                  <td style="padding:13px 20px;text-align:right;border-bottom:1px solid #27272a;">
                    <span style="display:inline-block;background:#052e16;color:#86efac;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500;">{category.upper()}</span>
                  </td>
                </tr>
                <tr>
                  <td style="padding:13px 20px;color:#71717a;font-size:13px;border-bottom:1px solid #27272a;vertical-align:top;padding-top:15px;">觸發條件</td>
                  <td style="padding:13px 20px;color:{accent};font-size:13px;font-weight:600;text-align:right;border-bottom:1px solid #27272a;">{trigger_condition}</td>
                </tr>
                <tr>
                  <td style="padding:16px 20px;color:#71717a;font-size:13px;{'border-bottom:1px solid #27272a;' if current_rsi is not None else ''}vertical-align:middle;">目前價格</td>
                  <td style="padding:16px 20px;text-align:right;{'border-bottom:1px solid #27272a;' if current_rsi is not None else ''}">
                    <span style="color:{price_accent};font-size:30px;font-weight:700;letter-spacing:-1px;">{current_price:.2f}</span>
                  </td>
                </tr>
                {rsi_row_html}
              </table>
            </td>
          </tr>

          <!-- CTA Button -->
          <tr>
            <td align="center" style="padding:28px 32px 32px;">
              <a href="{settings.app_base_url}/tracking"
                 style="display:inline-block;padding:13px 40px;background:linear-gradient(135deg,#22c55e 0%,#16a34a 100%);color:#ffffff;text-decoration:none;border-radius:50px;font-size:14px;font-weight:600;letter-spacing:0.3px;box-shadow:0 4px 16px rgba(34,197,94,0.3);">
                查看追蹤清單
              </a>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 32px;border-top:1px solid #1f1f23;text-align:center;">
              <p style="color:#52525b;font-size:12px;margin:0 0 6px;line-height:1.5;">此信件為系統自動發送，請勿直接回覆。</p>
              <p style="font-size:12px;margin:0 0 10px;">
                想要停止此項目的通知？
                <a href="{settings.backend_base_url}/api/public/stop-notification/{tracking_id}"
                   style="color:#ef4444;text-decoration:none;font-weight:500;">點此停止通知</a>
              </p>
              <p style="color:#3f3f46;font-size:11px;margin:0;">© 2026 NEXUS Finance Dashboard</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return subject, body

