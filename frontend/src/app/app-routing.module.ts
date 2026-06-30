import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ManutencaoComponent } from './manutencao/manutencao.component';

const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'consultor-externo' },
  { path: 'manutencao', component: ManutencaoComponent },
  {
    path: 'consultor-externo',
    loadChildren: () =>
      import('./publico/publico.module').then((module) => module.PublicoModule),
  },
  { path: 'tcc', pathMatch: 'full', redirectTo: 'consultor-externo' },
  { path: 'tcc/:id', redirectTo: 'consultor-externo/:id' },
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
  { path: '**', redirectTo: 'consultor-externo' },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, {
      anchorScrolling: 'enabled',
      scrollPositionRestoration: 'enabled',
    }),
  ],
  exports: [RouterModule],
})
export class AppRoutingModule {}
