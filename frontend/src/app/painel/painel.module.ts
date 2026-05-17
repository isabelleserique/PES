import { NgModule } from '@angular/core';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatSelectModule } from '@angular/material/select';
import { MatStepperModule } from '@angular/material/stepper';

import { SharedModule } from '../shared/shared.module';
import { PainelNavComponent } from './components/painel-nav/painel-nav.component';
import { PainelAlunoComponent } from './pages/aluno/aluno.component';
import { CriarPeriodoComponent } from './pages/criar-periodo/criar-periodo.component';
import { AceiteOrientacaoComponent } from './pages/aceite-orientacao/aceite-orientacao.component';
import { DefinirTccComponent } from './pages/definir-tcc/definir-tcc.component';
import { GerenciarPeriodosComponent } from './pages/gerenciar-periodos/gerenciar-periodos.component';
import { HistoricoSubmissoesComponent } from './pages/historico-submissoes/historico-submissoes.component';
import { PrazosPeriodoComponent } from './pages/prazos-periodo/prazos-periodo.component';
import { PainelCoordenadorComponent } from './pages/painel/painel.component';
import { PainelRedirectComponent } from './pages/redirect/redirect.component';
import { PainelOrientadorComponent } from './pages/orientador/orientador.component';
import { SubmeterArtigoComponent } from './pages/submeter-artigo/submeter-artigo.component';
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
  ],
  imports: [
    SharedModule,
    PainelRoutingModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatCheckboxModule,
    MatSelectModule,
    MatStepperModule,
  ],
})
export class PainelModule {}
