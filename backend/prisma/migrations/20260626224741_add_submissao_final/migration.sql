-- CreateEnum
CREATE TYPE "StatusDeposicao" AS ENUM ('AGUARDANDO_ENVIO', 'EM_REVISAO', 'DEVOLVIDO_PARA_CORRECAO', 'APROVADO', 'DEPOSITADO');

-- CreateEnum
CREATE TYPE "TipoDocumentoDeposicao" AS ENUM ('TCC_FINAL', 'ATA_DEFESA', 'TERMO_PUBLICACAO', 'NADA_CONSTA_BIBLIOTECA');

-- CreateTable
CREATE TABLE "depositos_finais" (
    "id" TEXT NOT NULL,
    "tcc_id" TEXT NOT NULL,
    "status" "StatusDeposicao" NOT NULL DEFAULT 'AGUARDANDO_ENVIO',
    "submetido_em" TIMESTAMP(3),
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "atualizado_em" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "depositos_finais_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "documentos_deposito" (
    "id" TEXT NOT NULL,
    "deposito_id" TEXT NOT NULL,
    "tipo_documento" "TipoDocumentoDeposicao" NOT NULL,
    "nome_original" TEXT NOT NULL,
    "caminho_original" TEXT NOT NULL,
    "mime_type" TEXT,
    "tamanho_bytes" INTEGER NOT NULL,
    "caminho_preview_pdf" TEXT,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "documentos_deposito_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "depositos_finais_tcc_id_key" ON "depositos_finais"("tcc_id");

-- CreateIndex
CREATE INDEX "depositos_finais_status_idx" ON "depositos_finais"("status");

-- CreateIndex
CREATE INDEX "documentos_deposito_deposito_id_idx" ON "documentos_deposito"("deposito_id");

-- CreateIndex
CREATE UNIQUE INDEX "documentos_deposito_deposito_id_tipo_documento_key" ON "documentos_deposito"("deposito_id", "tipo_documento");

-- AddForeignKey
ALTER TABLE "depositos_finais" ADD CONSTRAINT "depositos_finais_tcc_id_fkey" FOREIGN KEY ("tcc_id") REFERENCES "tccs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "documentos_deposito" ADD CONSTRAINT "documentos_deposito_deposito_id_fkey" FOREIGN KEY ("deposito_id") REFERENCES "depositos_finais"("id") ON DELETE CASCADE ON UPDATE CASCADE;
