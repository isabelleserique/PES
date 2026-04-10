# Guia do Projeto

Este guia foi escrito para quem ainda não tem costume com projetos full stack. A ideia é explicar o que existe nesta pasta, como as partes se conectam e quais comandos rodar para subir tudo sem precisar adivinhar.

## Visão geral

Este sistema foi dividido em cinco blocos principais:

1. `frontend/`
Interface Angular que roda no navegador.
2. `backend/`
API em FastAPI que recebe as requisições do frontend, aplica regras de negócio e conversa com banco e e-mail.
3. `backend/prisma/`
Camada de schema e migrations do banco PostgreSQL.
4. `docker-compose.yml`
Forma rápida de subir o PostgreSQL localmente.
5. `docs/`
Documentação do projeto, setup e fluxo de trabalho.

## Como as partes se conversam

Quando o sistema estiver rodando, o fluxo normal é este:

1. A pessoa usuária abre o frontend Angular no navegador.
2. O Angular envia uma requisição HTTP para a API FastAPI.
3. O backend valida os dados e executa a regra de negócio.
4. Se precisar salvar ou consultar dados, o backend usa o PostgreSQL.
5. Se precisar enviar e-mail, o backend usa SMTP do Gmail.
6. O backend devolve a resposta para o frontend.
7. O frontend mostra a resposta na tela.

Resumo rápido:

- `frontend` mostra a interface.
- `backend` decide o que fazer.
- `postgres` guarda os dados.
- `prisma` controla a estrutura do banco.
- `smtp` envia e-mails.

## Estrutura de pastas

### Raiz do projeto

- `.env.example`
Exemplo das variáveis principais do sistema.
- `.github/workflows/ci.yml`
Workflow de integração contínua.
- `docker-compose.yml`
Sobe o PostgreSQL local.
- `README.md`
Resumo rápido do projeto.
- `docs/`
Documentação detalhada.

### `backend/`

- `requirements.txt`
Dependências Python do backend.
- `package.json`
Dependências Node usadas pelo Prisma.
- `.env.example`
Exemplo mínimo das variáveis que o Prisma precisa.
- `app/main.py`
Ponto de entrada da API FastAPI.
- `app/api/router.py`
Router principal que registra as rotas.
- `app/routers/`
Rotas da aplicação.
- `app/core/config.py`
Leitura centralizada das variáveis de ambiente.
- `app/models/`
Modelos internos do domínio.
- `app/schemas/`
Schemas de entrada e saída da API.
- `app/services/`
Serviços reutilizáveis, como envio de e-mail.
- `scripts/`
Scripts utilitários, como teste de SMTP.
- `tests/`
Testes automatizados.
- `prisma/schema.prisma`
Modelo do banco.
- `prisma/migrations/`
Histórico das migrations do banco.

### `frontend/`

- `package.json`
Dependências e scripts do Angular.
- `angular.json`
Configuração do build Angular.
- `src/main.ts`
Entrada do frontend.
- `src/app/app.module.ts`
Módulo raiz do Angular.
- `src/app/app-routing.module.ts`
Rotas principais do frontend.
- `src/app/auth/`
Módulo de autenticação.
- `src/app/auth/pages/login/`
Tela placeholder de login.
- `src/app/shared/`
Módulo compartilhado para código reutilizável.
- `src/environments/`
URLs e flags por ambiente.
- `src/styles.css`
Estilos globais.

## O que cada módulo faz

### Backend

- `main.py`
Cria a aplicação FastAPI e registra as rotas.
- `core/config.py`
Carrega variáveis do `.env`, como porta, banco, JWT e SMTP.
- `routers/health.py`
Expõe `GET /health` para verificar se a API está viva.
- `schemas/health.py`
Define o formato da resposta do health check.
- `models/user.py`
Representa a ideia de usuário no domínio.
- `services/email_service.py`
Encapsula o envio de e-mails com Gmail SMTP.
- `scripts/send_test_email.py`
Permite testar o envio de e-mail sem depender de outras histórias.

### Frontend

- `AppModule`
Módulo raiz do Angular.
- `AppRoutingModule`
Decide para onde a aplicação navega.
- `AuthModule`
Agrupa o que é relacionado a login e autenticação.
- `SharedModule`
Lugar para componentes, pipes e módulos reutilizáveis.
- `LoginComponent`
Tela inicial de login para evoluir nas próximas histórias.

### Banco e Prisma

- `schema.prisma`
Define as tabelas e enums do banco.
- `migrations/`
Guarda as mudanças já aplicadas no banco.
- `prisma validate`
Confere se o schema está válido.
- `prisma migrate dev`
Cria e aplica migrations no banco local.
- `prisma studio`
Abre uma interface para visualizar os dados.

## Pré-requisitos

Antes de rodar o projeto, cada pessoa precisa ter:

- Python 3.12 ou compatível
- Node.js com npm
- Git
- Docker Desktop

Se quiser checar rapidamente:

```powershell
python --version
node -v
npm.cmd -v
git --version
docker --version
```

## Passo a passo para rodar o sistema

### 1. Criar os arquivos de ambiente

Na raiz do projeto:

```powershell
Copy-Item .env.example .env
```

Dentro do backend, para o Prisma:

```powershell
Copy-Item backend\.env.example backend\.env
```

Observação importante:

- O `backend/.env` é usado pelo Prisma.
- O `.env` da raiz é usado pelo backend FastAPI.
- Os dois precisam estar consistentes na parte do banco.

### 2. Subir o PostgreSQL

```powershell
docker compose up -d db
```

Para verificar se o container subiu:

```powershell
docker ps
```

### 3. Instalar dependências do backend Python

Criar a virtualenv:

```powershell
python -m venv .venv
```

Ativar no PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instalar dependências:

```powershell
pip install -r backend\requirements.txt
```

### 4. Instalar dependências do Prisma

```powershell
cd backend
npm.cmd install
cd ..
```

### 5. Validar e aplicar o schema do banco

Dentro de `backend/`:

```powershell
.\node_modules\.bin\prisma.cmd validate
.\node_modules\.bin\prisma.cmd migrate dev --name init
.\node_modules\.bin\prisma.cmd studio
```

O que cada comando faz:

- `validate`
Confere se o schema está correto.
- `migrate dev`
Aplica a estrutura no banco local.
- `studio`
Abre uma tela para ver os dados do banco.

### 6. Rodar o backend

Na raiz do projeto:

```powershell
uvicorn backend.app.main:app --reload
```

Teste rápido no navegador ou terminal:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
```

### 7. Instalar dependências do frontend

```powershell
cd frontend
npm.cmd install
cd ..
```

### 8. Rodar o frontend

```powershell
cd frontend
npm.cmd run start
```

Por padrão, a aplicação abre em:

- `http://localhost:4200`

### 9. Testar o SMTP Gmail

Na raiz do projeto, depois de preencher `SMTP_USER`, `SMTP_PASS` e `SMTP_FROM` no `.env`:

```powershell
python backend\scripts\send_test_email.py --subject "Teste SMTP" --body "SMTP funcionando."
```

## Ordem recomendada para ligar tudo

Se quiser evitar confusão, siga esta ordem:

1. Suba o banco com Docker.
2. Aplique o schema com Prisma.
3. Suba o backend FastAPI.
4. Suba o frontend Angular.
5. Teste a integração pelo navegador.

## Como saber se está tudo certo

Checklist simples:

- `docker ps` mostra o PostgreSQL rodando.
- `GET /health` responde com status `ok`.
- `npm.cmd run build` do frontend termina sem erro.
- `http://localhost:4200` abre a tela de login.
- O script de SMTP envia um e-mail de teste.

## Comandos úteis do dia a dia

### Backend

```powershell
pytest backend\tests
uvicorn backend.app.main:app --reload
python backend\scripts\send_test_email.py
```

### Frontend

```powershell
cd frontend
npm.cmd run start
npm.cmd run build
```

### Prisma

```powershell
cd backend
.\node_modules\.bin\prisma.cmd validate
.\node_modules\.bin\prisma.cmd migrate dev --name nome-da-migration
.\node_modules\.bin\prisma.cmd studio
```

## Problemas comuns

### `npm` bloqueado no PowerShell

Em algumas máquinas o PowerShell bloqueia `npm` por política de execução. Nesse caso, use:

```powershell
npm.cmd install
npm.cmd run start
```

### Prisma não acha o banco

Normalmente é um destes problemas:

- O PostgreSQL não está rodando.
- `backend/.env` não existe.
- `DATABASE_URL` e `DIRECT_URL` estão erradas.

### Backend sobe, mas frontend não conversa com ele

Confira:

- Se o backend está em `http://localhost:8000`
- Se o `environment.ts` aponta para a URL certa
- Se o navegador não está chamando outra porta

### SMTP não envia

Confira:

- Se a conta Gmail tem 2FA ativa
- Se a senha usada é App Password, não a senha normal
- Se `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` e `SMTP_PASS` estão preenchidas

## Fluxo de trabalho do time

Mesmo para quem ainda está começando, este é um fluxo saudável:

1. Atualizar o projeto.
2. Criar ou trocar para a branch da tarefa.
3. Rodar backend, banco e frontend localmente.
4. Fazer a alteração.
5. Rodar os testes e validações.
6. Abrir PR para integração.

## O que já foi validado neste ambiente

Até agora, nesta máquina, ficou confirmado:

- Instalação de `Node.js`, `npm` e `Git`
- `npm install` em `backend/`
- `npm install` em `frontend/`
- `npm run build` em `frontend/`
- `pytest backend/tests` com sucesso

Ficou para validação manual posterior:

- subir o frontend com `ng serve`
- aplicar `prisma migrate dev` em um PostgreSQL rodando localmente
- configurar proteção de branch no GitHub remoto

## Em caso de dúvida

Se alguém do time travar, o melhor caminho é verificar nesta ordem:

1. O banco está rodando?
2. Os arquivos `.env` existem?
3. O backend respondeu em `/health`?
4. O frontend compilou?
5. O comando foi rodado na pasta certa?

Esse tipo de projeto parece muita coisa no começo, mas na prática ele vira um ritual repetível: ligar banco, subir backend, subir frontend e testar a integração.

