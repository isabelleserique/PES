import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { AuthGuard } from '../auth/guards/auth.guard';
import { ProfileGuard } from '../auth/guards/profile.guard';
import { AceiteOrientacaoComponent } from './pages/aceite-orientacao/aceite-orientacao.component';
import { PainelAdminComponent } from './pages/admin/admin.component';
import { PainelAlunoComponent } from './pages/aluno/aluno.component';
import { CriarPeriodoComponent } from './pages/criar-periodo/criar-periodo.component';
import { DefinirTccComponent } from './pages/definir-tcc/definir-tcc.component';
import { GerenciarPeriodosComponent } from './pages/gerenciar-periodos/gerenciar-periodos.component';
import { HistoricoSubmissoesComponent } from './pages/historico-submissoes/historico-submissoes.component';
import { LogsSistemaComponent } from './pages/logs-sistema/logs-sistema.component';
import { NotificacoesComponent } from './pages/notificacoes/notificacoes.component';
import { PrazosPeriodoComponent } from './pages/prazos-periodo/prazos-periodo.component';
import { PrivacidadeComponent } from './pages/privacidade/privacidade.component';
import { PainelCoordenadorComponent } from './pages/painel/painel.component';
import { RegistrarBancaComponent } from './pages/registrar-banca/registrar-banca.component';
import { RegistrarSessaoComponent } from './pages/registrar-sessao/registrar-sessao.component';
import { PainelRedirectComponent } from './pages/redirect/redirect.component';
import { PainelOrientadorComponent } from './pages/orientador/orientador.component';
import { StatusDepositoComponent } from './pages/status-deposito/status-deposito.component';
import { SubmissoesAtrasadasComponent } from './pages/submissoes-atrasadas/submissoes-atrasadas.component';
import { SubmeterArtigoComponent } from './pages/submeter-artigo/submeter-artigo.component';
import { SubmeterVersaoFinalComponent } from './pages/submeter-versao-final/submeter-versao-final.component';
import { VisaoGeralComponent } from './pages/visao-geral/visao-geral.component';

const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    canActivate: [AuthGuard],
    component: PainelRedirectComponent,
  },
  {
    path: 'admin',
    component: PainelAdminComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ADMIN' },
  },
  {
    path: 'coordenador',
    component: PainelCoordenadorComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'COORDENADOR' },
  },
  {
    path: 'criar-periodo',
    component: CriarPeriodoComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'COORDENADOR' },
  },
  {
    path: 'criar-periodo/:periodoId',
    component: CriarPeriodoComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'COORDENADOR' },
  },
  {
    path: 'gerenciar-periodos',
    component: GerenciarPeriodosComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'COORDENADOR' },
  },
  {
    path: 'visao-geral',
    component: VisaoGeralComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'COORDENADOR' },
  },
  {
    path: 'prazos-periodo',
    component: PrazosPeriodoComponent,
    canActivate: [AuthGuard],
  },
  {
    path: 'definir-tcc',
    component: DefinirTccComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ALUNO' },
  },
  {
    path: 'submeter-entregaveis',
    component: SubmeterArtigoComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ALUNO' },
  },
  {
    path: 'submeter-versao-final',
    component: SubmeterVersaoFinalComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ALUNO' },
  },
  {
    path: 'status-deposito',
    component: StatusDepositoComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ALUNO' },
  },
  {
    path: 'privacidade',
    component: PrivacidadeComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ALUNO' },
  },
  {
    path: 'notificacoes',
    component: NotificacoesComponent,
    canActivate: [AuthGuard],
  },
  {
    path: 'historico-submissoes',
    component: HistoricoSubmissoesComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfis: ['COORDENADOR', 'ORIENTADOR'] },
  },
  {
    path: 'submissoes-atrasadas',
    component: SubmissoesAtrasadasComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'COORDENADOR' },
  },
  {
    path: 'logs-sistema',
    component: LogsSistemaComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ADMIN' },
  },
  {
    path: 'aceite-orientacao',
    component: AceiteOrientacaoComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ORIENTADOR' },
  },
  {
    path: 'registrar-sessao',
    component: RegistrarSessaoComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ORIENTADOR' },
  },
  {
    path: 'registrar-banca',
    component: RegistrarBancaComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ORIENTADOR' },
  },
  {
    path: 'aluno',
    component: PainelAlunoComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ALUNO' },
  },
  {
    path: 'orientador',
    component: PainelOrientadorComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ORIENTADOR' },
  },
  {
    path: 'registrar-apresentacao',
    redirectTo: 'submeter-entregaveis',
    pathMatch: 'full',
  },
  {
    path: '**',
    component: PainelRedirectComponent,
    canActivate: [AuthGuard],
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PainelRoutingModule {}
