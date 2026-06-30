ALTER TABLE "tccs" ALTER COLUMN "orientador_id" DROP NOT NULL;

ALTER TABLE "submissoes_entregaveis"
ADD COLUMN "nota_orientador" DOUBLE PRECISION,
ADD COLUMN "avaliado_por_id" TEXT,
ADD COLUMN "avaliado_em" TIMESTAMP(3);

CREATE INDEX "submissoes_entregaveis_avaliado_por_id_idx" ON "submissoes_entregaveis"("avaliado_por_id");

ALTER TABLE "submissoes_entregaveis"
ADD CONSTRAINT "submissoes_entregaveis_avaliado_por_id_fkey"
FOREIGN KEY ("avaliado_por_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
