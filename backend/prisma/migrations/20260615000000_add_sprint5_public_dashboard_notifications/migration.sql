ALTER TABLE "tccs"
    ADD COLUMN "resumo" TEXT,
    ADD COLUMN "area_tematica" TEXT,
    ADD COLUMN "curso" TEXT NOT NULL DEFAULT 'Ciência da Computação',
    ADD COLUMN "data_defesa" DATE,
    ADD COLUMN "banca" JSONB;

CREATE INDEX "tccs_area_tematica_idx" ON "tccs"("area_tematica");
CREATE INDEX "tccs_curso_idx" ON "tccs"("curso");
CREATE INDEX "tccs_data_defesa_idx" ON "tccs"("data_defesa");

CREATE TABLE "notificacoes_prazos" (
    "id" TEXT NOT NULL,
    "tcc_id" TEXT NOT NULL,
    "aluno_id" TEXT NOT NULL,
    "prazo_id" TEXT NOT NULL,
    "tipo_alerta" TEXT NOT NULL,
    "canal" TEXT NOT NULL DEFAULT 'EMAIL',
    "enviado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "notificacoes_prazos_pkey" PRIMARY KEY ("id")
);

ALTER TABLE "notificacoes_prazos"
    ADD CONSTRAINT "uq_notificacoes_prazos_tcc_prazo_tipo"
    UNIQUE ("tcc_id", "prazo_id", "tipo_alerta");

CREATE INDEX "notificacoes_prazos_tcc_id_idx" ON "notificacoes_prazos"("tcc_id");
CREATE INDEX "notificacoes_prazos_aluno_id_idx" ON "notificacoes_prazos"("aluno_id");
CREATE INDEX "notificacoes_prazos_prazo_id_idx" ON "notificacoes_prazos"("prazo_id");
CREATE INDEX "notificacoes_prazos_tipo_alerta_idx" ON "notificacoes_prazos"("tipo_alerta");
CREATE INDEX "notificacoes_prazos_enviado_em_idx" ON "notificacoes_prazos"("enviado_em");

ALTER TABLE "notificacoes_prazos"
    ADD CONSTRAINT "notificacoes_prazos_tcc_id_fkey"
    FOREIGN KEY ("tcc_id") REFERENCES "tccs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "notificacoes_prazos"
    ADD CONSTRAINT "notificacoes_prazos_aluno_id_fkey"
    FOREIGN KEY ("aluno_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "notificacoes_prazos"
    ADD CONSTRAINT "notificacoes_prazos_prazo_id_fkey"
    FOREIGN KEY ("prazo_id") REFERENCES "prazos_etapas"("id") ON DELETE CASCADE ON UPDATE CASCADE;
