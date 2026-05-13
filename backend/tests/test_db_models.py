from backend.app.db.models import PrazoEtapaRecord, TCCRecord


def test_tipo_tcc_sqlalchemy_enum_uses_database_values() -> None:
    expected_values = ["Todos", "Monografia", "Artigo", "Relatorio de Estagio"]

    assert PrazoEtapaRecord.__table__.c.tipo_tcc.type.enums == expected_values
    assert TCCRecord.__table__.c.tipo_tcc.type.enums == expected_values
