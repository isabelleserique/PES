CREATE TABLE "submissoes_entregaveis" (
    "id" TEXT NOT NULL,
    "tcc_id" TEXT NOT NULL,
    "aluno_id" TEXT NOT NULL,
    "tipo_tcc" "TipoTCC" NOT NULL,
    "etapa" TEXT NOT NULL,
    "versao" INTEGER NOT NULL,
    "nome_arquivo" TEXT NOT NULL,
    "caminho_arquivo" TEXT NOT NULL,
    "tipo_conteudo" TEXT,
    "tamanho_bytes" INTEGER NOT NULL,
    "foi_aceito" BOOLEAN NOT NULL DEFAULT false,
    "nome_comprovante" TEXT,
    "caminho_comprovante" TEXT,
    "tipo_conteudo_comprovante" TEXT,
    "tamanho_comprovante_bytes" INTEGER,
    "fora_do_prazo" BOOLEAN NOT NULL DEFAULT false,
    "nota_automatica" INTEGER,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "submissoes_entregaveis_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "uq_submissoes_entregaveis_tcc_etapa_versao" ON "submissoes_entregaveis"("tcc_id", "etapa", "versao");
CREATE INDEX "submissoes_entregaveis_tcc_id_idx" ON "submissoes_entregaveis"("tcc_id");
CREATE INDEX "submissoes_entregaveis_aluno_id_idx" ON "submissoes_entregaveis"("aluno_id");

ALTER TABLE "submissoes_entregaveis"
    ADD CONSTRAINT "submissoes_entregaveis_tcc_id_fkey"
    FOREIGN KEY ("tcc_id") REFERENCES "tccs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "submissoes_entregaveis"
    ADD CONSTRAINT "submissoes_entregaveis_aluno_id_fkey"
    FOREIGN KEY ("aluno_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
