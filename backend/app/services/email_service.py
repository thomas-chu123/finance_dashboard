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
) -> tuple[str, str]:
    direction_label = "突破" if trigger_direction == "above" else "跌破"
    mode_desc = {
        "price": "價格",
        "rsi": "RSI 指標",
        "both": "價格及 RSI",
        "either": "價格或 RSI",
    }.get(trigger_mode, "價格")
    
    subject = f"📊 投資提醒：{name} ({symbol}) 已{direction_label} {trigger_price:.2f}"

    primary = "#34a853"
    accent = "#ea4335" if trigger_direction == "below" else "#0f9d58"
    bg = "#f8f9fa"

    # RSI 信息行（可選）
    rsi_row = ""
    if current_rsi is not None:
        rsi_color = "#ea4335" if current_rsi < 30 else "#0f9d58" if current_rsi > 70 else "#4285f4"
        rsi_row = f"""
              <tr><td style="padding:8px 0;color:#5f6368;font-size:14px;">RSI (14)</td>
                  <td style="padding:8px 0;text-align:right;font-size:18px;font-weight:700;color:{rsi_color};">{current_rsi:.2f}</td></tr>
        """
        if rsi_below is not None and rsi_above is not None:
            rsi_row += f"""
              <tr><td style="padding:8px 0;color:#5f6368;font-size:14px;">RSI 閾值</td>
                  <td style="padding:8px 0;text-align:right;font-size:13px;color:#666;">超賣 {rsi_below:.0f} / 超買 {rsi_above:.0f}</td></tr>
            """

    body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;font-family:'Helvetica Neue',Arial,sans-serif;background:{bg};">
      <div style="max-width:600px;margin:20px auto;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);background:#fff;">
        <div style="background:linear-gradient(135deg,{primary} 0%,#2d8e47 100%);padding:30px;text-align:center;">
          <div style="font-size:48px;margin-bottom:10px;">📊</div>
          <h1 style="color:#fff;margin:0;font-size:22px;font-weight:600;">{mode_desc}觸發通知</h1>
        </div>
        <div style="padding:30px;">
          <p style="color:#5f6368;font-size:15px;">您追蹤的指數已達到您設定的觸發條件：</p>
          <div style="background:{bg};border-radius:12px;padding:24px;margin:20px 0;">
            <table style="width:100%;border-collapse:collapse;">
              <tr><td style="padding:8px 0;color:#5f6368;font-size:14px;">代碼</td>
                  <td style="padding:8px 0;text-align:right;font-weight:600;">{symbol}</td></tr>
              <tr><td style="padding:8px 0;color:#5f6368;font-size:14px;">名稱</td>
                  <td style="padding:8px 0;text-align:right;font-weight:600;">{name}</td></tr>
              <tr><td style="padding:8px 0;color:#5f6368;font-size:14px;">類別</td>
                  <td style="padding:8px 0;text-align:right;font-weight:600;">{category.upper()}</td></tr>
              <tr><td style="padding:8px 0;color:#5f6368;font-size:14px;">觸發條件</td>
                  <td style="padding:8px 0;text-align:right;font-weight:600;color:{accent};">{direction_label} {trigger_price:.2f}</td></tr>
              <tr><td style="padding:8px 0;color:#5f6368;font-size:14px;">目前價格</td>
                  <td style="padding:8px 0;text-align:right;font-size:24px;font-weight:700;color:{accent};">{current_price:.2f}</td></tr>
              {rsi_row}
            </table>
          </div>
          <div style="text-align:center;margin-top:24px;">
            <a href="{settings.app_base_url}/tracking" style="display:inline-block;padding:14px 32px;background:#34a853;color:#fff;text-decoration:none;border-radius:28px;font-weight:600;">查看追蹤清單</a>
          </div>
        </div>
        <div style="padding:20px;border-top:1px solid #f1f3f4;text-align:center;color:#70757a;font-size:12px;">
          <p style="margin:0;">此信件為系統自動發送，請勿直接回覆。</p>
          <p style="margin:6px 0;">想要停止此項目的通知？<a href="{settings.backend_base_url}/api/public/stop-notification/{tracking_id}" style="color:#ea4335;text-decoration:none;font-weight:600;">點此停止通知</a></p>
          <p style="margin:6px 0 0;">© 2026 NEXUS Finance Dashboard</p>
        </div>
      </div>
    </body>
    </html>
    """
    return subject, body

