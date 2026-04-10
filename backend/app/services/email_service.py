import logging
import smtplib
from email.message import EmailMessage

from backend.app.core.config import Settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_email(self, to_email: str, subject: str, body: str) -> None:
        if not self.settings.smtp_user or not self.settings.smtp_pass:
            raise ValueError("SMTP_USER e SMTP_PASS precisam estar configurados.")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.smtp_from or self.settings.smtp_user
        message["To"] = to_email
        message.set_content(body)

        if self.settings.smtp_port == 465:
            with smtplib.SMTP_SSL(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=self.settings.smtp_timeout_seconds,
            ) as smtp:
                smtp.login(self.settings.smtp_user, self.settings.smtp_pass)
                smtp.send_message(message)
            return

        with smtplib.SMTP(
            self.settings.smtp_host,
            self.settings.smtp_port,
            timeout=self.settings.smtp_timeout_seconds,
        ) as smtp:
            smtp.ehlo()
            if self.settings.smtp_use_tls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(self.settings.smtp_user, self.settings.smtp_pass)
            smtp.send_message(message)

    def send_welcome_email(self, to_email: str, full_name: str, username: str) -> bool:
        subject = "Bem-vindo ao Sistema TCC ICOMP"
        body = (
            f"Olá, {full_name}!\n\n"
            f"Seu usuário foi criado com sucesso.\n"
            f"Username: {username}\n"
            "No primeiro acesso, confirme seus dados e altere a senha provisória.\n"
        )

        try:
            self.send_email(to_email=to_email, subject=subject, body=body)
        except Exception:
            logger.exception("Falha ao enviar e-mail de boas-vindas para %s", to_email)
            return False

        return True

