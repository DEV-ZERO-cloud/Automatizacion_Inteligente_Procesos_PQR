import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from ..core.config import settings


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"[EMAIL MOCK] To: {to_email}")
        print(f"[EMAIL MOCK] Subject: {subject}")
        print(f"[EMAIL MOCK] Content: {html_content[:100]}...")
        return True
    
    message = MIMEMultipart("alternative")
    message["From"] = settings.EMAILS_FROM
    message["To"] = to_email
    message["Subject"] = subject
    
    if text_content:
        message.attach(MIMEText(text_content, "plain"))
    message.attach(MIMEText(html_content, "html"))
    
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def get_email_template_pqr_creada(pqr_id: int, titulo: str) -> tuple:
    subject = f"PQR ##{pqr_id} creada exitosamente"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #fafafa; padding: 20px; }}
            .container {{ background: white; border-radius: 12px; padding: 30px; max-width: 600px; margin: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: #E60023; color: white; padding: 20px; border-radius: 12px 12px 0 0; margin: -30px -30px 20px -30px; }}
            .content {{ color: #333; line-height: 1.6; }}
            .highlight {{ background: #FFECEC; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .footer {{ color: #767676; font-size: 12px; margin-top: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 24px;">Nueva PQR Creada</h1>
            </div>
            <div class="content">
                <div class="highlight">
                    <strong>PQR ##{pqr_id}</strong><br>
                    <strong>Título:</strong> {titulo}
                </div>
                <p>Tu solicitud ha sido recibida y está siendo procesada. Te notificaremos cuando haya actualizaciones.</p>
                <p>Puedes hacer seguimiento a tu PQR en cualquier momento desde nuestra plataforma.</p>
            </div>
            <div class="footer">
                Sistema de PQR's - ProjectProbe
            </div>
        </div>
    </body>
    </html>
    """
    return subject, html


def get_email_template_pqr_actualizada(pqr_id: int, titulo: str, nuevo_estado: str) -> tuple:
    estado_display = {
        "creado": "Creada",
        "en_proceso": "En Proceso",
        "resuelto": "Resuelta"
    }.get(nuevo_estado, nuevo_estado)
    
    subject = f"PQR ##{pqr_id} - Estado actualizado a {estado_display}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #fafafa; padding: 20px; }}
            .container {{ background: white; border-radius: 12px; padding: 30px; max-width: 600px; margin: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: #E60023; color: white; padding: 20px; border-radius: 12px 12px 0 0; margin: -30px -30px 20px -30px; }}
            .status-badge {{ display: inline-block; background: #00A67E; color: white; padding: 8px 20px; border-radius: 20px; font-weight: bold; }}
            .content {{ color: #333; line-height: 1.6; }}
            .footer {{ color: #767676; font-size: 12px; margin-top: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 24px;">Actualización de PQR</h1>
            </div>
            <div class="content">
                <p><strong>PQR ##{pqr_id}</strong></p>
                <p><strong>Título:</strong> {titulo}</p>
                <p><strong>Nuevo Estado:</strong> <span class="status-badge">{estado_display}</span></p>
                <p>Tu PQR ha sido actualizada. Ingresa a la plataforma para ver más detalles.</p>
            </div>
            <div class="footer">
                Sistema de PQR's - ProjectProbe
            </div>
        </div>
    </body>
    </html>
    """
    return subject, html


def get_email_template_nuevo_comentario(pqr_id: int, titulo: str, comentario: str) -> tuple:
    subject = f"PQR ##{pqr_id} - Nuevo comentario"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #fafafa; padding: 20px; }}
            .container {{ background: white; border-radius: 12px; padding: 30px; max-width: 600px; margin: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: #E60023; color: white; padding: 20px; border-radius: 12px 12px 0 0; margin: -30px -30px 20px -30px; }}
            .comment-box {{ background: #f5f5f5; padding: 15px; border-radius: 8px; border-left: 4px solid #E60023; margin: 15px 0; }}
            .content {{ color: #333; line-height: 1.6; }}
            .footer {{ color: #767676; font-size: 12px; margin-top: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 24px;">Nuevo Comentario</h1>
            </div>
            <div class="content">
                <p><strong>PQR ##{pqr_id}</strong></p>
                <p><strong>Título:</strong> {titulo}</p>
                <div class="comment-box">
                    <strong>Comentario:</strong><br>
                    {comentario}
                </div>
            </div>
            <div class="footer">
                Sistema de PQR's - ProjectProbe
            </div>
        </div>
    </body>
    </html>
    """
    return subject, html
