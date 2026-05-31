import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from backend.app.core.config import get_settings

settings = get_settings()

class BackupService:
    def __init__(self):
        self.base_dir = Path(settings.upload_dir) / "backups"
        self.daily_dir = self.base_dir / "daily"
        self.logs_dir = self.base_dir / "logs"
        self.submissoes_dir = Path(settings.upload_dir) / "submissoes-entregaveis"

        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.daily_dir.mkdir(parents=True, exist_ok=True)

    def _backup_database(self, backup_path: Path):
        db_dump_file = backup_path / "db_dump.sql"
        command = [
            "pg_dump",
            settings.database_url,
            "-f",
            str(db_dump_file),
        ]
        try:
            subprocess.run(command, check=True)
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar backup do banco: {e}")

    def _backup_files(self, backup_path: Path):
        target = backup_path / "submissoes-entregaveis"
        if self.submissoes_dir.exists():
            shutil.copytree(self.submissoes_dir, target)

    def _write_log(self, message: str):
        log_file = self.logs_dir / f"backup_{datetime.now().date()}.log"
        timestamp = datetime.now().isoformat()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def run_backup(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_path = self.daily_dir / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)

        try:
            self._backup_database(backup_path)
            self._backup_files(backup_path)
            self._write_log(f"Backup concluído com sucesso: {timestamp}")
            self._cleanup_old_backups()
        except Exception as e:
            self._write_log(f"ERRO no backup: {str(e)}")

    def _cleanup_old_backups(self):
        """Remove backups mais antigos que 30 dias."""
        retention_days = 30
        now = datetime.now()

        for backup in self.daily_dir.iterdir():
            if backup.is_dir():
                backup_time = datetime.strptime(backup.name, "%Y-%m-%d_%H%M%S")
                if now - backup_time > timedelta(days=retention_days):
                    shutil.rmtree(backup, ignore_errors=True)
                    self._write_log(f"Backup antigo removido: {backup.name}")

    def restore_backup(self, backup_timestamp: str):
        backup_path = self.daily_dir / backup_timestamp
        if not backup_path.exists():
            raise FileNotFoundError("Backup não encontrado")

        submissoes_backup = backup_path / "submissoes-entregaveis"
        if submissoes_backup.exists():
            if self.submissoes_dir.exists():
                shutil.rmtree(self.submissoes_dir)
            shutil.copytree(submissoes_backup, self.submissoes_dir)

        db_dump = backup_path / "db_dump.sql"
        if db_dump.exists():
            command = [
                "psql",
                settings.database_url,
                "-f",
                str(db_dump),
            ]
            subprocess.run(command, check=True)

        self._write_log(f"Restauração executada: {backup_timestamp}")

backup_service = BackupService()