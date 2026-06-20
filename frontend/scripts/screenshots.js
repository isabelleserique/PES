/* Captura prints das telas do Luiz Daniel mockando a API e forjando a sessão. */
const { chromium } = require('playwright');
const path = require('path');

const BASE = 'http://localhost:4200';
const OUT = path.resolve(__dirname, '../../prints-us');

const sessao = (perfil, nome = 'Luiz Daniel') => ({
  access_token: 'mock-token',
  token_type: 'bearer',
  expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  user: { id: 'u-luiz', nome_completo: nome, email: 'luiz.daniel@icomp.ufam.edu.br', perfil },
});

const cronograma = {
  periodo: { id: 'p1', nome: '2026/1', data_inicio: '2026-03-01', data_fim: '2026-07-31', ativo: true },
  perfil: 'ORIENTADOR',
  aluno: null,
  orientandos: [
    { aluno_id: 'a1', aluno_nome: 'Mariana Souza', matricula: '21950001', titulo_tcc: 'Detecção de fraudes com aprendizado de máquina', tipo_tcc: 'Monografia', status_tcc: 'EM_ANDAMENTO', prazo_excedido: false, alerta_prazo: null, papel_orientacao: 'ORIENTADOR', prazos: [] },
    { aluno_id: 'a2', aluno_nome: 'Carlos Henrique', matricula: '21950002', titulo_tcc: 'Otimização de rotas urbanas', tipo_tcc: 'Artigo', status_tcc: 'EM_ANDAMENTO', prazo_excedido: false, alerta_prazo: null, papel_orientacao: 'ORIENTADOR', prazos: [] },
  ],
  filtro_orientando_id: null,
};

const meuTcc = {
  id: 't1', titulo: 'Detecção de fraudes com aprendizado de máquina', tipo_tcc: 'Monografia',
  orientador_id: 'o1', orientador_nome: 'Prof. Luiz Daniel', coorientador_id: null, coorientador_nome: null,
  periodo_id: 'p1', periodo_nome: '2026/1', status: 'EM_ANDAMENTO', prazo_excedido: false,
  alerta_prazo: null, observacao_orientador: null, criado_em: '2026-03-10T10:00:00Z', atualizado_em: '2026-03-10T10:00:00Z',
};

const deposito = {
  id: 'd1', aluno_id: 'a-luiz', aluno_nome: 'Luiz Daniel', titulo_tcc: 'Detecção de fraudes com aprendizado de máquina',
  status: 'EM_REVISAO', versao_final_nome: 'tcc-versao-final.pdf',
  documentos: [
    { tipo: 'ATA_DEFESA', nome_arquivo: 'ata-defesa.pdf', enviado_em: '2026-06-15T12:00:00Z' },
    { tipo: 'FOLHA_APROVACAO', nome_arquivo: 'folha-aprovacao-assinada.pdf', enviado_em: '2026-06-15T12:00:00Z' },
  ],
  observacao_revisao: null, atualizado_em: '2026-06-16T09:00:00Z',
};

const prefs = { email_prazos_orientandos: true, antecedencia_dias: 7, email_notas_parciais: true, email_notas_finais: true };
const consentimento = { publicar_portal_publico: true, compartilhar_terceiros: false, atualizado_em: '2026-06-18T14:30:00Z' };

const professores = [
  { id: 'p1', nome: 'Profa. Maria Oliveira', titulacao: 'Doutora', area_atuacao: 'Inteligência Artificial', instituicao: 'IComp/UFAM', total_orientacoes: 12 },
  { id: 'p2', nome: 'Prof. João Mendes', titulacao: 'Doutor', area_atuacao: 'Engenharia de Software', instituicao: 'IComp/UFAM', total_orientacoes: 8 },
  { id: 'p3', nome: 'Profa. Ana Beatriz', titulacao: 'Doutora', area_atuacao: 'Redes de Computadores', instituicao: 'IComp/UFAM', total_orientacoes: 5 },
];

const professorDetalhe = {
  id: 'p1', nome: 'Profa. Maria Oliveira', titulacao: 'Doutora em Ciência da Computação',
  area_atuacao: 'Inteligência Artificial', instituicao: 'IComp/UFAM', total_orientacoes: 12,
  email: 'maria.oliveira@icomp.ufam.edu.br', lattes_url: 'http://lattes.cnpq.br/0000000000000000',
  bio: 'Professora associada do Instituto de Computação, atua em aprendizado de máquina, visão computacional e processamento de linguagem natural.',
  areas: ['Inteligência Artificial', 'Aprendizado de Máquina', 'Visão Computacional', 'PLN'],
  tccs_orientados: [
    { id: 't1', titulo: 'Detecção de fraudes com aprendizado de máquina', tipo_tcc: 'Monografia', ano: 2025, aluno_nome: 'Mariana Souza' },
    { id: 't2', titulo: 'Classificação de imagens médicas com redes neurais', tipo_tcc: 'Artigo', ano: 2024, aluno_nome: 'Pedro Lima' },
    { id: 't3', titulo: 'Análise de sentimentos em redes sociais', tipo_tcc: 'Monografia', ano: 2024, aluno_nome: 'Júlia Ramos' },
  ],
};

const telas = [
  { nome: 'US024-registrar-banca', perfil: 'ORIENTADOR', rota: '/painel/registrar-banca', mocks: { '**/periodos/ativo/cronograma**': cronograma } },
  { nome: 'US026-US027-submeter-versao-final', perfil: 'ALUNO', rota: '/painel/submeter-versao-final', mocks: { '**/tcc/me': meuTcc } },
  { nome: 'US028-status-deposito', perfil: 'ALUNO', rota: '/painel/status-deposito', mocks: { '**/biblioteca/deposito/me': deposito } },
  { nome: 'US030-notificacoes-orientador', perfil: 'ORIENTADOR', rota: '/painel/notificacoes', mocks: { '**/notificacoes/preferencias': prefs } },
  { nome: 'US031-notificacoes-aluno', perfil: 'ALUNO', rota: '/painel/notificacoes', mocks: { '**/notificacoes/preferencias': prefs } },
  { nome: 'US038-privacidade', perfil: 'ALUNO', rota: '/painel/privacidade', mocks: { '**/privacidade/consentimento': consentimento } },
  { nome: 'US045-responsivo-mobile', perfil: 'ALUNO', rota: '/painel/submeter-versao-final', mocks: { '**/tcc/me': meuTcc }, viewport: { width: 390, height: 844 } },
  { nome: 'US005-listar-professores', perfil: 'ALUNO', rota: '/tcc/professores', mocks: { '**/public/professores': professores }, click: 'button[type="submit"]' },
  { nome: 'US005-detalhe-professor', perfil: 'ALUNO', rota: '/tcc/professores/p1', mocks: { '**/public/professores/*': professorDetalhe } },
];

(async () => {
  const browser = await chromium.launch();
  for (const t of telas) {
    const context = await browser.newContext({ viewport: t.viewport || { width: 1366, height: 900 } });
    await context.addInitScript((s) => {
      window.localStorage.setItem('tccomp.auth.session', s);
    }, JSON.stringify(sessao(t.perfil)));

    const page = await context.newPage();
    for (const [pattern, body] of Object.entries(t.mocks)) {
      await page.route(pattern, (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) }));
    }

    await page.goto(`${BASE}${t.rota}`, { waitUntil: 'networkidle' });
    if (t.click) {
      await page.click(t.click);
      await page.waitForTimeout(600);
    }
    await page.waitForTimeout(1200);
    const file = path.join(OUT, `${t.nome}.png`);
    await page.screenshot({ path: file, fullPage: !t.viewport });
    console.log(`✔ ${t.nome}.png`);
    await context.close();
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
