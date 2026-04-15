import logging
import smtplib
from email.message import EmailMessage

from backend.app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_welcome_email_body(self, full_name: str, username: str, temporary_password: str) -> str:
        return (
            f"Olá, {full_name}!\n\n"
            f"Seu usuário foi criado com sucesso.\n"
            f"Username: {username}\n"
            f"Senha temporária: {temporary_password}\n"
            "No primeiro acesso, confirme seus dados e altere a senha provisória.\n"
        )

    def build_registration_approved_email_body(self, full_name: str, username: str) -> str:
        return (
            f"Olá, {full_name}!\n\n"
            "Seu cadastro no Sistema TCC ICOMP foi aprovado.\n"
            f"Username: {username}\n"
            "Você já pode acessar o sistema com a senha definida no auto-cadastro.\n"
        )

    def build_pending_registration_notification_body(
        self,
        requester_name: str,
        requester_email: str,
        requester_username: str,
        requester_profile: str,
    ) -> str:
        return (
            "Há uma nova solicitação de cadastro pendente no Sistema TCC ICOMP.\n\n"
            f"Nome: {requester_name}\n"
            f"E-mail: {requester_email}\n"
            f"Username: {requester_username}\n"
            f"Perfil: {requester_profile}\n"
        )

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

    def send_welcome_email(
        self,
        to_email: str,
        full_name: str,
        username: str,
        temporary_password: str,
    ) -> bool:
        subject = "Bem-vindo ao Sistema TCC ICOMP"
        body = self.build_welcome_email_body(
            full_name=full_name,
            username=username,
            temporary_password=temporary_password,
        )

        try:
            self.send_email(to_email=to_email, subject=subject, body=body)
        except Exception:
            logger.exception("Falha ao enviar e-mail de boas-vindas para %s", to_email)
            return False

        return True

    def send_registration_approved_email(
        self,
        to_email: str,
        full_name: str,
        username: str,
    ) -> bool:
        subject = "Cadastro aprovado no Sistema TCC ICOMP"
        body = self.build_registration_approved_email_body(
            full_name=full_name,
            username=username,
        )

        try:
            self.send_email(to_email=to_email, subject=subject, body=body)
        except Exception:
            logger.exception("Falha ao enviar e-mail de aprovação para %s", to_email)
            return False

        return True

    def send_pending_registration_notification(
        self,
        to_email: str,
        requester_name: str,
        requester_email: str,
        requester_username: str,
        requester_profile: str,
    ) -> bool:
        subject = "Nova solicitação de cadastro pendente"
        body = self.build_pending_registration_notification_body(
            requester_name=requester_name,
            requester_email=requester_email,
            requester_username=requester_username,
            requester_profile=requester_profile,
        )

        try:
            self.send_email(to_email=to_email, subject=subject, body=body)
        except Exception:
            logger.exception("Falha ao notificar coordenador sobre solicitação pendente para %s", to_email)
            return False

        return True

async def get_email_service() -> EmailService:
    return EmailService(get_settings())
