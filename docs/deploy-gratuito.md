# Deploy gratuito para apresentacao

Este caminho prioriza velocidade para demonstracao: frontend na Vercel, backend no Render e banco PostgreSQL no Supabase. Os arquivos enviados ficam temporarios no Render enquanto o storage definitivo nao for configurado.

## 1. Banco no Supabase

1. Crie um projeto gratuito no Supabase.
2. Copie a string PostgreSQL do projeto.
3. Use essa string em `DATABASE_URL` e `DIRECT_URL` no Render.
4. Se usar connection pooling, deixe `DIRECT_URL` com a conexao direta para o Prisma aplicar migrations.

## 2. Backend no Render

1. Suba o repositorio para o GitHub.
2. No Render, crie um Blueprint apontando para este repositorio. O Render vai ler `render.yaml`.
3. Preencha as variaveis marcadas como `sync: false`.

Variaveis obrigatorias:

```env
DATABASE_URL=postgresql://...
DIRECT_URL=postgresql://...
FRONTEND_URL=https://SEU-FRONTEND.vercel.app
CORS_ORIGINS=https://SEU-FRONTEND.vercel.app
API_BASE_URL=https://SEU-BACKEND.onrender.com
```

O `JWT_SECRET` e gerado automaticamente pelo Render no blueprint. Se configurar manualmente, gere um valor forte:

```bash
openssl rand -hex 32
```

O deploy usa Docker porque o backend precisa de Python e Node/Prisma no mesmo ambiente. Na inicializacao, o container executa `prisma migrate deploy` antes de subir o FastAPI.

## 3. Frontend na Vercel

1. Importe o mesmo repositorio na Vercel.
2. Configure o Root Directory como `frontend`.
3. Configure a variavel de ambiente:

```env
API_URL=https://SEU-BACKEND.onrender.com
```

O `frontend/vercel.json` ja define:

```bash
npm run build:deploy
```

e tambem configura fallback de rotas Angular para `index.html`.

## 4. Usuario administrador

Depois do backend estar online, crie o admin no Render Shell:

```bash
ADMIN_EMAIL=admin@exemplo.com \
ADMIN_USERNAME=admin \
ADMIN_FULL_NAME="Administrador" \
ADMIN_PASSWORD="troque-essa-senha" \
python backend/scripts/create_admin_user.py
```

Troque a senha no primeiro uso pratico e nao versiona credenciais reais.

## 5. Teste rapido

1. Acesse `https://SEU-BACKEND.onrender.com/health`.
2. Acesse o frontend na Vercel.
3. Faça login.
4. Cadastre ou valide usuarios.
5. Crie um periodo letivo.
6. Faça uma submissao simples.

## Limitacao conhecida

Enquanto `UPLOAD_DIR=/tmp/tccomp-storage`, arquivos enviados podem sumir quando o Render reiniciar ou redeployar. Para apresentacao isso pode ser aceitavel. Para uso real, mova uploads para Supabase Storage, S3 ou outro storage persistente.
