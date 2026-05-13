# Relatorio de Casos de Teste - US006 a US009

Data da validacao: 04/05/2026

Fontes utilizadas:
- [Casos de Teste.pdf](</home/iserique/Downloads/Casos de Teste.pdf>)
- [backend/tests/test_periodos.py](/home/iserique/Downloads/PES/backend/tests/test_periodos.py)
- [backend/tests/test_tcc.py](/home/iserique/Downloads/PES/backend/tests/test_tcc.py)

Evidencias executadas nesta validacao:
- `./.venvpes/bin/python -m pytest backend/tests/test_periodos.py backend/tests/test_tcc.py` -> `20 passed`
- `npm run build` no frontend -> concluido com sucesso

## Casos de teste do PDF

| ID Caso de Teste | US | Descricao do Caso de Teste | Resultado Obtido | Status |
| --- | --- | --- | --- | --- |
| 12 | US006 | Criar novo periodo letivo | O endpoint `POST /periodos` retornou `201`, criou o periodo `2025.1`, marcou status ativo e persistiu os prazos configurados. | Aprovado |
| 13 | US006 | Tentar criar periodo sobreposto | O sistema bloqueou a criacao com `409` e mensagem de conflito para intervalo ja utilizado. | Aprovado |
| 14 | US007 | Visualizar prazos do periodo atual como aluno | O endpoint `GET /periodos/ativo/cronograma` retornou apenas os prazos aplicaveis ao tipo de TCC do aluno, com status visual e cor. | Aprovado |
| 15 | US007 no PDF, correspondente a US008 na implementacao | Indicar tema e orientador | O endpoint `POST /tcc/me` salvou titulo, tipo e orientador, registrou o TCC no periodo ativo e disparou notificacao ao orientador via servico de e-mail. | Aprovado |
| 16 | US008 | Informar TCC fora do prazo | O sistema permitiu o envio, marcou `prazo_excedido = true` e retornou `alerta_prazo` para sinalizar atraso. | Aprovado |
| 17 | US008 no PDF, correspondente a US009 na implementacao | Aceitar orientacao | O endpoint `PATCH /tcc/orientacoes/{id}/decisao` com acao `ACEITAR` atualizou o status para `EM_ANDAMENTO`, registrou a observacao e notificou o aluno. | Aprovado |
| 18 | US009 | Recusar orientacao com motivo | A recusa sem observacao retornou `422`. Com observacao valida, o sistema atualizou o status para `SEM_ORIENTADOR` e notificou o aluno com o motivo informado. | Aprovado |
| 19 | US009 | Rastreabilidade de acoes | O sistema gerou log em banco por meio de `TCCEditLogRecord` e registrou auditoria da decisao com acao, decisor e contexto de prazo. | Aprovado |
| 20 | US006 / US007 / US008 / US009 | Bloqueio de upload de arquivo invalido | Nao foi possivel executar. O fluxo de upload de pre-projeto nao existe na implementacao atual dessas US, entao nao ha endpoint nem validacao de extensao para exercitar este caso. | Nao aplicavel / Pendente |

## Casos complementares automatizados

| ID Caso de Teste | US | Descricao do Caso de Teste | Resultado Obtido | Status |
| --- | --- | --- | --- | --- |
| CT-EX01 | US006 | Impedir segundo periodo ativo | O sistema retornou `409` ao tentar criar um novo periodo com `ativo = true` enquanto outro periodo ativo ja existia. | Aprovado |
| CT-EX02 | US006 | Impedir prazo fora do intervalo do periodo | O sistema retornou `422` quando um prazo foi informado fora do intervalo entre `data_inicio` e `data_fim`. | Aprovado |
| CT-EX03 | US006 | Impedir edicao de periodo inativo | O sistema retornou `409` e manteve os dados originais do periodo inativo. | Aprovado |
| CT-EX04 | US007 | Exibir visao do orientador agrupada por orientandos | O cronograma do orientador foi retornado agrupado por orientando, com filtro por `orientando_id` e alertas de atraso. | Aprovado |
| CT-EX05 | US008 | Impedir segundo envio de TCC no mesmo periodo | O sistema retornou `409` ao tentar criar um segundo TCC para o mesmo aluno no periodo ativo. | Aprovado |
| CT-EX06 | US008 | Registrar edicao de TCC e reenviar para aceite | A edicao atualizou os dados, registrou log de alteracao e resetou o status para `AGUARDANDO_ACEITE`. | Aprovado |
| CT-EX07 | US009 | Listar apenas solicitacoes pendentes do orientador autenticado | O sistema retornou somente solicitacoes do orientador logado, incluindo sinalizacao de submissao fora do prazo e decisao fora do prazo. | Aprovado |
| CT-EX08 | US009 | Bloquear decisao por orientador diferente do vinculado | O sistema retornou `404` para tentativa de aceite por outro orientador. | Aprovado |

## Analise dos Resultados

- Dos 9 casos listados no PDF para o recorte US006 a US009, 8 foram aprovados e 1 permaneceu pendente por ausencia do modulo de upload.
- A cobertura automatizada validou os fluxos de sucesso, erros de regra de negocio, controle de permissao, acoes fora do prazo e rastreabilidade.
- A integracao de frontend foi validada em nivel de compilacao com `ng build`, o que confirma consistencia estrutural das telas e dos contratos HTTP usados pelo painel do aluno e do orientador.
- Em termos de custo-beneficio, a implementacao reaproveitou o mesmo fluxo de `TCC` para formalizacao e decisao de orientacao, evitando duplicar entidades de solicitacao e reduzindo custo de manutencao.
- O PDF apresenta divergencia de classificacao em dois itens: o caso 15 esta rotulado como US007, mas corresponde ao comportamento da US008; o caso 17 esta rotulado como US008, mas corresponde ao comportamento da US009.

## Problemas Encontrados

- Nao foram encontrados erros funcionais criticos nos casos automatizados executados em 04/05/2026.
- Existe divergencia entre a numeracao/classificacao do PDF e a divisao funcional implementada no sistema para US007, US008 e US009.
- O caso 20 nao pode ser executado porque o sistema ainda nao possui fluxo de upload de pre-projeto nesta entrega.

## Limitacoes do Sistema

- As notificacoes por e-mail foram validadas com servico de teste/stub, nao com um provedor SMTP real.
- Nao ha testes E2E automatizados do frontend com navegacao real, apenas validacao de build e testes de integracao do backend.
- O sistema ainda nao implementa upload e validacao de extensao para arquivos de pre-projeto, portanto o comportamento esperado no caso 20 continua pendente.
- Nao foram executados testes de carga, concorrencia ou compatibilidade entre navegadores para esse conjunto de US.
