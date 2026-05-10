import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { AuthGuard } from '../auth/guards/auth.guard';
import { ProfileGuard } from '../auth/guards/profile.guard';
import { PainelAlunoComponent } from './pages/aluno/aluno.component';
import { CriarPeriodoComponent } from './pages/criar-periodo/criar-periodo.component';
import { AceiteOrientacaoComponent } from './pages/aceite-orientacao/aceite-orientacao.component';
import { DefinirTccComponent } from './pages/definir-tcc/definir-tcc.component';
import { PrazosPeriodoComponent } from './pages/prazos-periodo/prazos-periodo.component';
import { PainelCoordenadorComponent } from './pages/painel/painel.component';
import { PainelRedirectComponent } from './pages/redirect/redirect.component';
import { PainelOrientadorComponent } from './pages/orientador/orientador.component';
import { SubmeterArtigoComponent } from './pages/submeter-artigo/submeter-artigo.component';

const routes: Routes = [
  {
    path: '',
    canActivate: [AuthGuard],
    component: PainelRedirectComponent,
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
    path: 'aceite-orientacao',
    component: AceiteOrientacaoComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ORIENTADOR' },
  },
  {
    path: 'submeter-artigo',
    component: SubmeterArtigoComponent,
    canActivate: [AuthGuard, ProfileGuard],
    data: { perfil: 'ALUNO' },
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
