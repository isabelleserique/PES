CREATE TYPE "TipoTCC" AS ENUM ('Todos', 'Monografia', 'Artigo');

CREATE TABLE "periodos_letivos" (
    "id" TEXT NOT NULL,
    "nome" TEXT NOT NULL,
    "data_inicio" DATE NOT NULL,
    "data_fim" DATE NOT NULL,
    "ativo" BOOLEAN NOT NULL DEFAULT false,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "atualizado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "periodos_letivos_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "prazos_etapas" (
    "id" TEXT NOT NULL,
    "periodo_id" TEXT NOT NULL,
    "nome_etapa" TEXT NOT NULL,
    "data_limite" DATE NOT NULL,
    "tipo_tcc" "TipoTCC" NOT NULL,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "prazos_etapas_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "prazos_etapas_periodo_id_fkey" FOREIGN KEY ("periodo_id") REFERENCES "periodos_letivos"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "periodos_letivos_nome_idx" ON "periodos_letivos"("nome");
CREATE INDEX "periodos_letivos_data_inicio_idx" ON "periodos_letivos"("data_inicio");
CREATE INDEX "periodos_letivos_data_fim_idx" ON "periodos_letivos"("data_fim");
CREATE INDEX "periodos_letivos_ativo_idx" ON "periodos_letivos"("ativo");
CREATE INDEX "prazos_etapas_periodo_id_idx" ON "prazos_etapas"("periodo_id");

CREATE UNIQUE INDEX "periodos_letivos_single_active_idx" ON "periodos_letivos"("ativo") WHERE "ativo" IS TRUE;
