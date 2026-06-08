import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ManutencaoComponent } from './manutencao/manutencao.component';

const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'auth/login' },
  { path: 'manutencao', component: ManutencaoComponent },
  {
    path: 'auth',
    loadChildren: () =>
      import('./auth/auth.module').then((module) => module.AuthModule),
  },
  {
    path: 'painel',
    loadChildren: () =>
      import('./painel/painel.module').then((module) => module.PainelModule),
  },
  {
    path: 'tcc',
    loadChildren: () =>
      import('./publico/publico.module').then((module) => module.PublicoModule),
  },
  { path: '**', redirectTo: 'auth/login' },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
