ALTER TABLE "users"
    ADD COLUMN "email_prazos_orientandos" BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN "notificacao_antecedencia_dias" INTEGER NOT NULL DEFAULT 3,
    ADD COLUMN "email_notas_parciais" BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN "email_notas_finais" BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN "publicar_tcc_portal_publico" BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN "compartilhar_dados_terceiros" BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN "privacidade_atualizado_em" TIMESTAMP(3);

CREATE TYPE "PapelBanca" AS ENUM (
    'ORIENTADOR',
    'COORIENTADOR',
    'AVALIADOR_INTERNO',
    'AVALIADOR_EXTERNO',
    'SUPLENTE'
);

CREATE TABLE "bancas" (
    "id" TEXT NOT NULL,
    "tcc_id" TEXT NOT NULL,
    "data_defesa" TIMESTAMP(3) NOT NULL,
    "local" TEXT NOT NULL,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "atualizado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "bancas_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "bancas_tcc_id_key" ON "bancas"("tcc_id");
CREATE INDEX "bancas_tcc_id_idx" ON "bancas"("tcc_id");

ALTER TABLE "bancas"
    ADD CONSTRAINT "bancas_tcc_id_fkey"
    FOREIGN KEY ("tcc_id") REFERENCES "tccs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

CREATE TABLE "membros_banca" (
    "id" TEXT NOT NULL,
    "banca_id" TEXT NOT NULL,
    "user_id" TEXT,
    "nome" TEXT NOT NULL,
    "titulacao" TEXT NOT NULL,
    "instituicao" TEXT NOT NULL,
    "papel" "PapelBanca" NOT NULL,

    CONSTRAINT "membros_banca_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "membros_banca_banca_id_idx" ON "membros_banca"("banca_id");
CREATE INDEX "membros_banca_user_id_idx" ON "membros_banca"("user_id");

ALTER TABLE "membros_banca"
    ADD CONSTRAINT "membros_banca_banca_id_fkey"
    FOREIGN KEY ("banca_id") REFERENCES "bancas"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "membros_banca"
    ADD CONSTRAINT "membros_banca_user_id_fkey"
    FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

CREATE TYPE "StatusDeposito" AS ENUM (
    'AGUARDANDO_ENVIO',
    'EM_REVISAO',
    'DEVOLVIDO_PARA_CORRECAO',
    'APROVADO',
    'DEPOSITADO'
);

CREATE TYPE "TipoDocumentoDeposito" AS ENUM (
    'TCC_FINAL',
    'ATA_DEFESA',
    'FOLHA_APROVACAO',
    'FORMULARIOS',
    'DECLARACOES'
);

CREATE TABLE "depositos_finais" (
    "id" TEXT NOT NULL,
    "tcc_id" TEXT NOT NULL,
    "status" "StatusDeposito" NOT NULL DEFAULT 'AGUARDANDO_ENVIO',
    "observacao_revisao" TEXT,
    "submetido_em" TIMESTAMP(3),
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "atualizado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "depositos_finais_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "depositos_finais_tcc_id_key" ON "depositos_finais"("tcc_id");
CREATE INDEX "depositos_finais_tcc_id_idx" ON "depositos_finais"("tcc_id");
CREATE INDEX "depositos_finais_status_idx" ON "depositos_finais"("status");

ALTER TABLE "depositos_finais"
    ADD CONSTRAINT "depositos_finais_tcc_id_fkey"
    FOREIGN KEY ("tcc_id") REFERENCES "tccs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

CREATE TABLE "documentos_deposito" (
    "id" TEXT NOT NULL,
    "deposito_id" TEXT NOT NULL,
    "tipo_documento" "TipoDocumentoDeposito" NOT NULL,
    "nome_original" TEXT NOT NULL,
    "caminho_original" TEXT NOT NULL,
    "mime_type" TEXT,
    "tamanho_bytes" INTEGER NOT NULL,
    "caminho_preview_pdf" TEXT,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "documentos_deposito_pkey" PRIMARY KEY ("id")
);

ALTER TABLE "documentos_deposito"
    ADD CONSTRAINT "uq_documento_deposito_tipo"
    UNIQUE ("deposito_id", "tipo_documento");

CREATE INDEX "documentos_deposito_deposito_id_idx" ON "documentos_deposito"("deposito_id");

ALTER TABLE "documentos_deposito"
    ADD CONSTRAINT "documentos_deposito_deposito_id_fkey"
    FOREIGN KEY ("deposito_id") REFERENCES "depositos_finais"("id") ON DELETE CASCADE ON UPDATE CASCADE;
