-- CreateEnum
CREATE TYPE "PapelBanca" AS ENUM ('ORIENTADOR', 'AVALIADOR_INTERNO', 'AVALIADOR_EXTERNO', 'SUPLENTE');

-- CreateTable
CREATE TABLE "bancas" (
    "id" TEXT NOT NULL,
    "tcc_id" TEXT NOT NULL,
    "data_defesa" TIMESTAMP(3) NOT NULL,
    "local" TEXT NOT NULL,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "bancas_pkey" PRIMARY KEY ("id")
);

-- CreateTable
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

-- CreateIndex
CREATE UNIQUE INDEX "bancas_tcc_id_key" ON "bancas"("tcc_id");

-- CreateIndex
CREATE INDEX "membros_banca_banca_id_idx" ON "membros_banca"("banca_id");

-- CreateIndex
CREATE INDEX "membros_banca_user_id_idx" ON "membros_banca"("user_id");

-- CreateIndex
CREATE UNIQUE INDEX "membros_banca_banca_id_papel_key" ON "membros_banca"("banca_id", "papel");

-- AddForeignKey
ALTER TABLE "bancas" ADD CONSTRAINT "bancas_tcc_id_fkey" FOREIGN KEY ("tcc_id") REFERENCES "tccs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "membros_banca" ADD CONSTRAINT "membros_banca_banca_id_fkey" FOREIGN KEY ("banca_id") REFERENCES "bancas"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "membros_banca" ADD CONSTRAINT "membros_banca_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- RenameIndex
ALTER INDEX "uq_submissoes_entregaveis_tcc_etapa_versao" RENAME TO "submissoes_entregaveis_tcc_id_etapa_versao_key";

-- RenameIndex
ALTER INDEX "uq_tcc_aluno_periodo" RENAME TO "tccs_aluno_id_periodo_id_key";
