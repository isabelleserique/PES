import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { AuthGuard } from '../auth/guards/auth.guard';
import { ProfileGuard } from '../auth/guards/profile.guard';
import { PainelAlunoComponent } from './pages/aluno/aluno.component';
import { PainelCoordenadorComponent } from './pages/painel/painel.component';
import { PainelRedirectComponent } from './pages/redirect/redirect.component';
import { PainelOrientadorComponent } from './pages/orientador/orientador.component';

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
