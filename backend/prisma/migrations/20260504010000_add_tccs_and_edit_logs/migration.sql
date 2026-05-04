ALTER TYPE "TipoTCC" ADD VALUE IF NOT EXISTS 'Relatorio de Estagio';

CREATE TYPE "StatusTCC" AS ENUM ('AGUARDANDO_ACEITE', 'EM_ANDAMENTO', 'APROVADO', 'REJEITADO');
CREATE TYPE "AcaoEdicaoTCC" AS ENUM ('CRIACAO', 'EDICAO');

CREATE TABLE "tccs" (
    "id" TEXT NOT NULL,
    "titulo" TEXT NOT NULL,
    "tipo_tcc" "TipoTCC" NOT NULL,
    "aluno_id" TEXT NOT NULL,
    "orientador_id" TEXT NOT NULL,
    "coorientador_id" TEXT,
    "periodo_id" TEXT NOT NULL,
    "status" "StatusTCC" NOT NULL DEFAULT 'AGUARDANDO_ACEITE',
    "prazo_excedido" BOOLEAN NOT NULL DEFAULT false,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "atualizado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "tccs_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "tccs_aluno_id_fkey" FOREIGN KEY ("aluno_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "tccs_orientador_id_fkey" FOREIGN KEY ("orientador_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "tccs_coorientador_id_fkey" FOREIGN KEY ("coorientador_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "tccs_periodo_id_fkey" FOREIGN KEY ("periodo_id") REFERENCES "periodos_letivos"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "tcc_edit_logs" (
    "id" TEXT NOT NULL,
    "tcc_id" TEXT NOT NULL,
    "actor_user_id" TEXT NOT NULL,
    "acao" "AcaoEdicaoTCC" NOT NULL,
    "dados_anteriores" JSONB,
    "dados_novos" JSONB NOT NULL,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "tcc_edit_logs_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "tcc_edit_logs_tcc_id_fkey" FOREIGN KEY ("tcc_id") REFERENCES "tccs"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "tcc_edit_logs_actor_user_id_fkey" FOREIGN KEY ("actor_user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "uq_tcc_aluno_periodo" ON "tccs"("aluno_id", "periodo_id");
CREATE INDEX "tccs_orientador_id_idx" ON "tccs"("orientador_id");
CREATE INDEX "tccs_coorientador_id_idx" ON "tccs"("coorientador_id");
CREATE INDEX "tccs_periodo_id_idx" ON "tccs"("periodo_id");
CREATE INDEX "tcc_edit_logs_tcc_id_idx" ON "tcc_edit_logs"("tcc_id");
CREATE INDEX "tcc_edit_logs_actor_user_id_idx" ON "tcc_edit_logs"("actor_user_id");
