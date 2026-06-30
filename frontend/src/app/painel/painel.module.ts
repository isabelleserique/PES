import { NgModule } from '@angular/core';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatStepperModule } from '@angular/material/stepper';

import { SharedModule } from '../shared/shared.module';
import { PainelNavComponent } from './components/painel-nav/painel-nav.component';
import { PainelAlunoComponent } from './pages/aluno/aluno.component';
import { CriarPeriodoComponent } from './pages/criar-periodo/criar-periodo.component';
import { AceiteOrientacaoComponent } from './pages/aceite-orientacao/aceite-orientacao.component';
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
import { PainelRoutingModule } from './painel-routing.module';

@NgModule({
  declarations: [
    PainelNavComponent,
    PainelCoordenadorComponent,
    PainelAlunoComponent,
    PainelOrientadorComponent,
    PainelRedirectComponent,
    CriarPeriodoComponent,
    GerenciarPeriodosComponent,
    PrazosPeriodoComponent,
    DefinirTccComponent,
    AceiteOrientacaoComponent,
    SubmeterArtigoComponent,
    HistoricoSubmissoesComponent,
    RegistrarSessaoComponent,
    RegistrarBancaComponent,
    SubmissoesAtrasadasComponent,
    LogsSistemaComponent,
    VisaoGeralComponent,
    SubmeterVersaoFinalComponent,
    StatusDepositoComponent,
    NotificacoesComponent,
    PrivacidadeComponent,
  ],
  imports: [
    SharedModule,
    PainelRoutingModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatCheckboxModule,
    MatSelectModule,
    MatStepperModule,
    MatSlideToggleModule,
  ],
})
export class PainelModule {}
