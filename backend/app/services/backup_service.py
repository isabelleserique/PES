from __future__ import annotations

import asyncio
import shutil
import subprocess
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from backend.app.core.config import Settings, get_settings


class BackupService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.backup_dir = self.settings.upload_dir / "backups"
        self.logs_dir = self.backup_dir / "logs"
        self.daily_dir = self.backup_dir / "daily"
        self.submissoes_dir = self.settings.upload_dir / "submissoes-entregaveis"

    def run_daily_backup(self) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        target_dir = self.daily_dir / timestamp
        target_dir.mkdir(parents=True, exist_ok=False)

        try:
            self._backup_database(target_dir)
            self._backup_files(target_dir)
            self._write_log(f"Backup concluido: {target_dir}")
            return target_dir
        except Exception as exc:
            self._write_log(f"Falha no backup {target_dir}: {exc}")
            raise

    def _backup_database(self, target_dir: Path) -> None:
        dump_path = target_dir / "database.sql"
        command = ["pg_dump", self.settings.database_url, "-f", str(dump_path)]
        subprocess.run(command, check=True, capture_output=True)

    def _backup_files(self, target_dir: Path) -> None:
        if not self.submissoes_dir.exists():
            return
        shutil.copytree(self.submissoes_dir, target_dir / "submissoes-entregaveis")

    def _write_log(self, message: str) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.logs_dir / f"backup-{datetime.now(UTC).date().isoformat()}.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{datetime.now(UTC).isoformat()}] {message}\n")


async def run_daily_backup_loop(
    *,
    backup_service: BackupService | None = None,
    backup_time: time = time(hour=2, minute=0),
) -> None:
    service = backup_service or BackupService()
    while True:
        await asyncio.sleep(_seconds_until_next_run(backup_time))
        await asyncio.to_thread(service.run_daily_backup)


def _seconds_until_next_run(backup_time: time) -> float:
    now = datetime.now(UTC)
    next_run = now.replace(
        hour=backup_time.hour,
        minute=backup_time.minute,
        second=backup_time.second,
        microsecond=0,
    )
    if next_run <= now:
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()
