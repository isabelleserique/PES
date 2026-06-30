from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.db.models import AuditLogRecord, UserRecord
from backend.app.db.session import SessionLocal
from backend.app.models.user import Perfil, StatusCadastro

DEV_ADMIN_EMAIL = "admin.sistema@icomp.ufam.edu.br"
DEV_ADMIN_USERNAME = "superadmin"
DEV_ADMIN_FULL_NAME = "Super Admin"
DEV_ADMIN_PASSWORD = "SuperSudo@123"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cria ou atualiza o usuario administrador do sistema.")
    parser.add_argument("--email")
    parser.add_argument("--username")
    parser.add_argument("--nome")
    parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    is_production = settings.app_env.strip().lower() == "production"
    password = args.password or settings.admin_password

    if not password and is_production:
        raise SystemExit("ADMIN_PASSWORD e obrigatorio quando APP_ENV=production.")

    if not password:
        password = DEV_ADMIN_PASSWORD

    if len(password) < 8:
        raise SystemExit("A senha do admin deve ter no minimo 8 caracteres.")

    email = (args.email or settings.admin_email or os.getenv("ADMIN_EMAIL") or DEV_ADMIN_EMAIL).strip().lower()
    username = (args.username or settings.admin_username or os.getenv("ADMIN_USERNAME") or DEV_ADMIN_USERNAME).strip().lower()
    nome = (args.nome or settings.admin_full_name or os.getenv("ADMIN_FULL_NAME") or DEV_ADMIN_FULL_NAME).strip()

    if not email or not username or not nome:
        raise SystemExit("ADMIN_EMAIL, ADMIN_USERNAME e ADMIN_FULL_NAME nao podem ficar vazios.")

    with SessionLocal() as session:
        users = session.scalars(
            select(UserRecord).where(
                or_(
                    UserRecord.email == email,
                    UserRecord.username == username,
                )
            )
        ).all()

        if len(users) > 1:
            raise SystemExit("Email e username pertencem a usuarios diferentes. Ajuste os dados antes de continuar.")

        if users:
            user = users[0]
            action = "atualizado"
        else:
            user = UserRecord(
                id=str(uuid4()),
                nome_completo=nome,
                email=email,
                username=username,
                senha_hash="",
                perfil=Perfil.ADMIN,
                matricula=None,
                status=StatusCadastro.ATIVO,
                failed_login_attempts=0,
                blocked_until=None,
                ativo=True,
            )
            session.add(user)
            action = "criado"

        user.nome_completo = nome
        user.email = email
        user.username = username
        user.senha_hash = hash_password(password)
        user.perfil = Perfil.ADMIN
        user.matricula = None
        user.status = StatusCadastro.ATIVO
        user.failed_login_attempts = 0
        user.blocked_until = None
        user.ativo = True

        session.add(
            AuditLogRecord(
                id=str(uuid4()),
                user_id=user.id,
                acao="PROVISIONAMENTO_ADMIN",
                entidade="USER",
                descricao=f"Usuario administrador {action} por script local.",
                dados={"email": email, "username": username},
                ip=None,
            )
        )

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise SystemExit("Nao foi possivel criar/atualizar o admin por conflito de dados.") from exc
        except SQLAlchemyError as exc:
            session.rollback()
            raise SystemExit(
                "Nao foi possivel criar/atualizar o admin. Verifique se as migracoes do banco foram aplicadas."
            ) from exc

    print(f"Admin {action}:")
    print(f"  email: {email}")
    print(f"  username: {username}")
    if password == DEV_ADMIN_PASSWORD:
        print(f"  senha local: {password}")
    else:
        print("  senha: definida por ADMIN_PASSWORD/--password")


if __name__ == "__main__":
    main()
