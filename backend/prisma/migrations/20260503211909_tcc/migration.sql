-- CreateEnum
CREATE TYPE "TipoTCC" AS ENUM ('MONOGRAFIA', 'ARTIGO', 'RELATORIO');

-- CreateEnum
CREATE TYPE "StatusTCC" AS ENUM ('RASCUNHO', 'AGUARDANDO_ACEITE', 'APROVADO', 'REJEITADO');

-- CreateTable
CREATE TABLE "tccs" (
    "id" TEXT NOT NULL,
    "titulo" TEXT NOT NULL,
    "tipo" "TipoTCC" NOT NULL,
    "aluno_id" TEXT NOT NULL,
    "orientador_id" TEXT NOT NULL,
    "coorientador_id" TEXT,
    "periodo" TEXT NOT NULL,
    "status" "StatusTCC" NOT NULL DEFAULT 'AGUARDANDO_ACEITE',
    "prazo_excedido" BOOLEAN NOT NULL DEFAULT false,
    "criado_em" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "atualizado_em" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "tccs_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "tccs_aluno_id_periodo_key" ON "tccs"("aluno_id", "periodo");
