"""Email notification service (adapted from medical project)."""
from __future__ import annotations
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

    # 依實際觸發條件決定強調色：使用 Nexus 綠 (#00D084) 為主，但跌破顯色略微區分
    is_bearish = (price_condition_met and trigger_direction == "below") or (
        rsi_condition_met and rsi_below is not None and current_rsi is not None and current_rsi < rsi_below
    )
    
    # 統一使用 NEXUS Green 作為主要 Brand Color
    nexus_green = "#00D084"
    nexus_dark_green = "#059669"
    nexus_light_green = "#ecfdf5"
    
    error_red = "#ef4444"
    error_light_red = "#fef2f2"
    
    # 動態調整狀態標籤顏色 (跌破用紅，其餘用綠)
    badge_bg = error_light_red if is_bearish else nexus_light_green
    badge_color = error_red if is_bearish else nexus_dark_green
    
    # 價格強調色
    price_accent = error_red if (trigger_direction == "below") else nexus_green

    # RSI 欄位 logic
    rsi_html = ""
    if current_rsi is not None:
        if rsi_below is not None and current_rsi < rsi_below:
            rsi_disp_color = error_red
            rsi_status_badge = '<span style="font-size:11px;background:#fee2e2;color:#ef4444;padding:2px 6px;border-radius:4px;margin-left:4px;vertical-align:middle;">超賣</span>'
        elif rsi_above is not None and current_rsi > rsi_above:
            rsi_disp_color = nexus_green
            rsi_status_badge = '<span style="font-size:11px;background:#dcfce7;color:#059669;padding:2px 6px;border-radius:4px;margin-left:4px;vertical-align:middle;">超買</span>'
        else:
            rsi_disp_color = "#3b82f6"
            rsi_status_badge = ""
        
        rsi_html = f"""
                                    <td width="50%" valign="top">
                                        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">目前 RSI</div>
                                        <div style="font-size: 24px; font-weight: 700; color: {rsi_disp_color};">{current_rsi:.2f}{rsi_status_badge}</div>
                                    </td>
        """

    body_style = f"margin: 0; padding: 0; font-family: 'Inter', 'Microsoft JhengHei', Helvetica, Arial, sans-serif; background-color: #f8fafc; color: {nexus_dark_green};"
    
    body = f"""<!DOCTYPE html>
<html lang="zh-TW" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light">
    <meta name="supported-color-schemes" content="light">
    <title>{subject}</title>
    <!--[if mso]>
    <xml>
        <o:OfficeDocumentSettings>
            <o:AllowPNG/>
            <o:PixelsPerInch>96</o:PixelsPerInch>
        </o:OfficeDocumentSettings>
    </xml>
    <![endif]-->
    <style>
        :root {{ color-scheme: light; supported-color-schemes: light; }}
        body {{ margin: 0; padding: 0; width: 100% !important; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; background-color: #f8fafc; }}
        img {{ line-height: 100%; outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; border: 0; height: auto; }}
        
        /* Dark Mode Protection */
        @media (prefers-color-scheme: dark) {{
            .body-wrapper {{ background-color: #f8fafc !important; }}
            .main-content {{ background-color: #ffffff !important; color: #334155 !important; }}
            .text-main {{ color: #334155 !important; }}
            .text-muted {{ color: #64748b !important; }}
            .data-card {{ background-color: #fcfdfe !important; border-color: #e2e8f0 !important; }}
        }}

        /* Responsive */
        @media only screen and (max-width: 600px) {{
            .main-content {{ border-radius: 0 !important; }}
            .content-padding {{ padding: 30px 20px !important; }}
        }}
    </style>
</head>
<body style="{body_style}">
    <div class="body-wrapper" style="background-color: #f8fafc; padding: 20px 0;">
        <center>
            <table class="main-content" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin: 0 auto;">
                <!-- Header / Logo -->
                <tr>
                    <td align="center" style="padding: 40px 30px 20px;">
                        <table border="0" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center" style="background-color: {nexus_green}; width: 56px; height: 56px; border-radius: 28px; color: #ffffff; font-size: 24px; font-weight: bold; box-shadow: 0 4px 12px rgba(0, 208, 132, 0.2);">
                                    N
                                </td>
                            </tr>
                        </table>
                        <h1 style="margin: 16px 0 4px; font-size: 28px; color: {nexus_green}; letter-spacing: 1px;">NEXUS</h1>
                        <p style="margin: 0; color: #64748b; font-size: 14px; font-weight: 500;">Finance Dashboard</p>
                    </td>
                </tr>

                <!-- Main Body -->
                <tr>
                    <td class="content-padding" style="padding: 20px 40px 40px;">
                        <div style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 12px; line-height: 1.4;">{subject}</div>
                        <div style="display: inline-block; background-color: {badge_bg}; color: {badge_color}; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-bottom: 24px;">
                            觸發項目：{mode_desc}
                        </div>
                        
                        <p class="text-muted" style="color: #64748b; font-size: 15px; line-height: 1.6; margin-bottom: 24px;">
                            您追蹤的投資標的已達到預設的觸發條件，請查看最新市場狀態：
                        </p>
                        
                        <!-- Data Card -->
                        <div class="data-card" style="background-color: #fcfdfe; border: 1.5px solid #e2e8f0; border-radius: 20px; padding: 24px; margin-bottom: 32px;">
                            <div style="font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                                {symbol} <span style="font-weight: 400; font-size: 14px; color: #64748b;">({name})</span>
                            </div>
                            <div style="color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px;">
                                資產類型：{category.upper()}
                            </div>
                            
                            <div style="color: {nexus_green}; font-weight: 600; font-size: 15px; padding: 12px 0; border-top: 1px dashed #e2e8f0; border-bottom: 1px dashed #e2e8f0; margin-bottom: 20px;">
                                ✓ 觸發條件：{trigger_condition}
                            </div>
                            
                            <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td width="50%" valign="top">
                                        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">目前價格</div>
                                        <div style="font-size: 24px; font-weight: 700; color: {price_accent};">{current_price:.2f}</div>
                                    </td>
                                    {rsi_html}
                                </tr>
                            </table>
                        </div>
                        <!-- CTA Button -->
                        <table border="0" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td align="center">
                                    <a href="{settings.app_base_url}/tracking" style="background-color: {nexus_green}; color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 12px; font-weight: 600; display: inline-block; font-size: 16px; box-shadow: 0 4px 15px rgba(0, 208, 132, 0.2);">
                                        立即進入儀表板查看
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>

                <!-- Footer -->
                <tr>
                    <td style="padding: 30px; text-align: center; font-size: 12px; color: #94a3b8; background-color: #f8fafc; border-top: 1px solid #e2e8f0;" align="center">
                        此郵件為系統自動發送，請勿直接回覆。<br>
                        想要停止此項目的通知？ <a href="{settings.backend_base_url}/api/public/stop-notification/{tracking_id}" style="color: {error_red}; text-decoration: none; font-weight: 600;">點此停止通知</a><br>
                        <div style="margin-top: 8px;">© 2026 NEXUS Finance Dashboard.</div>
                    </td>
                </tr>
            </table>
        </center>
    </div>
</body>
</html>"""
    return subject, body
