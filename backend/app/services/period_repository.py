from datetime import date


from datetime import date
from backend.app.models.prazo import Prazo


class PeriodRepository:

    def get_periodo_ativo(self):
        return {
            "id": 1,
            "nome": "2026.1",
            "status": "ATIVO",
        }

    def get_prazos_do_periodo_ativo(self) -> list[Prazo]:
        return [
            Prazo("Definição de tema", date(2026, 5, 10), "TODOS"),
            Prazo("Entrega parcial", date(2026, 5, 5), "ARTIGO"),
        ]