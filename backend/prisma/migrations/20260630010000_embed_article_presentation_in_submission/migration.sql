ALTER TABLE "apresentacoes_artigo"
    ADD COLUMN "submissao_id" TEXT,
    ADD COLUMN "tipo_veiculo" TEXT,
    ADD COLUMN "veiculo_publicacao" TEXT,
    ADD COLUMN "local_apresentacao" TEXT,
    ADD COLUMN "observacoes" TEXT;

CREATE INDEX "apresentacoes_artigo_submissao_id_idx" ON "apresentacoes_artigo"("submissao_id");

ALTER TABLE "apresentacoes_artigo"
    ADD CONSTRAINT "apresentacoes_artigo_submissao_id_fkey"
    FOREIGN KEY ("submissao_id") REFERENCES "submissoes_entregaveis"("id") ON DELETE SET NULL ON UPDATE CASCADE;
