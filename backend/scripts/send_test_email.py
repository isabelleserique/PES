import argparse

from backend.app.core.config import get_settings
from backend.app.services.email_service import EmailService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Envia um e-mail de teste via SMTP.")
    parser.add_argument("--to", dest="to_email", help="Destinatário do e-mail.")
    parser.add_argument("--subject", default="Teste SMTP - Sistema TCC ICOMP")
    parser.add_argument(
        "--body",
        default="E-mail de teste enviado com sucesso pela configuração SMTP do projeto.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    target = args.to_email or settings.smtp_test_recipient or settings.smtp_user

    if not target:
        raise SystemExit("Defina --to ou SMTP_TEST_RECIPIENT no .env.")

    service = EmailService(settings)
    service.send_email(to_email=target, subject=args.subject, body=args.body)
    print(f"E-mail enviado com sucesso para {target}.")


if __name__ == "__main__":
    main()

