# GitHub Setup

Este guia cobre os itens do card `SETUP-01` que dependem de Git e do repositório remoto.

## Proteger a branch `main`

No GitHub:

1. Abra `Settings > Branches`.
2. Crie uma ruleset para `main`.
3. Exija pull request antes de merge.
4. Exija pelo menos 1 aprovação.
5. Bloqueie push direto na `main`.

## Criar as branches do sprint

Quando o Git estiver disponível no ambiente e já existir pelo menos um commit no repositório:

```bash
git checkout -b dev
git checkout -b feature/us001
git checkout main
git checkout -b feature/us002
git checkout main
git checkout -b feature/us003
git checkout main
git checkout -b feature/us004
```

Sugestão prática:

- `main`: sempre estável
- `dev`: integração da sprint
- `feature/us00x`: trabalho de cada história

Observação:

- Sem repositório remoto no GitHub não existe proteção real de branch.
- Sem um primeiro commit, o Git ainda não consegue materializar todas as branches locais do fluxo.

## Próximo passo recomendado

Depois de publicar o repositório remoto, troque o badge local do `README.md` pelo badge real do GitHub Actions:

```md
![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)
```
