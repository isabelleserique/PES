CREATE TABLE "orientacao_sessoes" (
    "id" TEXT NOT NULL,
    "tcc_id" TEXT NOT NULL,
    "aluno_id" TEXT NOT NULL,
    "orientador_id" TEXT NOT NULL,
    "data_sessao" DATE NOT NULL,
    "resumo" TEXT NOT NULL,
    "proximos_passos" TEXT NOT NULL,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "orientacao_sessoes_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "apresentacoes_artigo" (
    "id" TEXT NOT NULL,
    "tcc_id" TEXT NOT NULL,
    "aluno_id" TEXT NOT NULL,
    "data_apresentacao" DATE NOT NULL,
    "artigo_ja_aceito" BOOLEAN NOT NULL DEFAULT false,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "apresentacoes_artigo_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "audit_logs" (
    "id" TEXT NOT NULL,
    "user_id" TEXT,
    "acao" TEXT NOT NULL,
    "entidade" TEXT,
    "descricao" TEXT NOT NULL,
    "dados" JSONB,
    "ip" TEXT,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "orientacao_sessoes_tcc_id_idx" ON "orientacao_sessoes"("tcc_id");
CREATE INDEX "orientacao_sessoes_aluno_id_idx" ON "orientacao_sessoes"("aluno_id");
CREATE INDEX "orientacao_sessoes_orientador_id_idx" ON "orientacao_sessoes"("orientador_id");
CREATE INDEX "apresentacoes_artigo_tcc_id_idx" ON "apresentacoes_artigo"("tcc_id");
CREATE INDEX "apresentacoes_artigo_aluno_id_idx" ON "apresentacoes_artigo"("aluno_id");
CREATE INDEX "audit_logs_user_id_idx" ON "audit_logs"("user_id");
CREATE INDEX "audit_logs_acao_idx" ON "audit_logs"("acao");
CREATE INDEX "audit_logs_entidade_idx" ON "audit_logs"("entidade");
CREATE INDEX "audit_logs_criado_em_idx" ON "audit_logs"("criado_em");

ALTER TABLE "orientacao_sessoes"
    ADD CONSTRAINT "orientacao_sessoes_tcc_id_fkey"
    FOREIGN KEY ("tcc_id") REFERENCES "tccs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "orientacao_sessoes"
    ADD CONSTRAINT "orientacao_sessoes_aluno_id_fkey"
    FOREIGN KEY ("aluno_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "orientacao_sessoes"
    ADD CONSTRAINT "orientacao_sessoes_orientador_id_fkey"
    FOREIGN KEY ("orientador_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "apresentacoes_artigo"
    ADD CONSTRAINT "apresentacoes_artigo_tcc_id_fkey"
    FOREIGN KEY ("tcc_id") REFERENCES "tccs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "apresentacoes_artigo"
    ADD CONSTRAINT "apresentacoes_artigo_aluno_id_fkey"
    FOREIGN KEY ("aluno_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "audit_logs"
    ADD CONSTRAINT "audit_logs_user_id_fkey"
    FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
