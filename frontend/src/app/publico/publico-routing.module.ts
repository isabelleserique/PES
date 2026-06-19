import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { BuscarTccComponent } from './pages/buscar-tcc/buscar-tcc.component';
import { DetalheTccComponent } from './pages/detalhe-tcc/detalhe-tcc.component';

const routes: Routes = [
  { path: '', component: BuscarTccComponent },
  { path: ':id', component: DetalheTccComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PublicoRoutingModule {}
