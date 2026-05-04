from datetime import date

from backend.app.db.models import UserRecord
from backend.app.models.user import Perfil
from backend.app.models.prazo import Prazo
from backend.app.services.period_repository import PeriodRepository


class PeriodService:
    def __init__(self):
        self.repo = PeriodRepository()

    def get_prazos_visiveis(self, current_user: UserRecord) -> dict:
        hoje = date.today()

        periodo = self.repo.get_periodo_ativo()
        prazos = self.repo.get_prazos_do_periodo_ativo()

        prazos_filtrados = [
            self._map_prazo(prazo, current_user, hoje)
            for prazo in prazos
            if self._pode_ver(prazo, current_user)
        ]

        return {
            "periodo": periodo,
            "prazos": prazos_filtrados,
        }

    def _pode_ver(self, prazo: Prazo, user: UserRecord) -> bool:
        if user.perfil == Perfil.ALUNO:
            return self._aluno_pode_ver(prazo, user)

        if user.perfil == Perfil.ORIENTADOR:
            return self._orientador_pode_ver(prazo, user)

        return False

    def _aluno_pode_ver(self, prazo: Prazo, user: UserRecord) -> bool:
        tipo_tcc_usuario = self._get_tipo_tcc_usuario(user)

        return (
            prazo.tipo_tcc == "TODOS"
            or prazo.tipo_tcc == tipo_tcc_usuario
        )

    def _orientador_pode_ver(self, prazo: Prazo, user: UserRecord) -> bool:
        return True  

    def _get_tipo_tcc_usuario(self, user: UserRecord) -> str:
        return getattr(user, "tipo_tcc", "ARTIGO")

    def _map_prazo(self, prazo: Prazo, user: UserRecord, hoje: date) -> dict:
        dias_restantes = (prazo.data_limite - hoje).days

        status, cor = self._status_info(dias_restantes)

        return {
            "nome": prazo.nome,
            "data_limite": prazo.data_limite.isoformat(),
            "tipo_tcc": prazo.tipo_tcc,
            "dias_restantes": dias_restantes,
            "status": status,
            "cor": cor,
            "mensagem": self._formatar_mensagem(dias_restantes),
        }

    def _status_info(self, dias: int) -> tuple[str, str]:
        if dias > 7:
            return "A_VENCER", "verde"
        if 1 <= dias <= 7:
            return "PROXIMO", "amarelo"
        if dias == 0:
            return "HOJE", "laranja"
        return "VENCIDO", "vermelho"

    def _formatar_mensagem(self, dias: int) -> str:
        if dias > 0:
            return f"Faltam {dias} dias"
        if dias == 0:
            return "Vence hoje"
        return f"Venceu há {abs(dias)} dias"

async def get_period_service() -> PeriodService:
    return PeriodService()