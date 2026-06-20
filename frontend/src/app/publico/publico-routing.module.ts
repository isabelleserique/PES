import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { BuscarTccComponent } from './pages/buscar-tcc/buscar-tcc.component';
import { DetalheTccComponent } from './pages/detalhe-tcc/detalhe-tcc.component';
import { ListarProfessoresComponent } from './pages/listar-professores/listar-professores.component';
import { DetalheProfessorComponent } from './pages/detalhe-professor/detalhe-professor.component';

const routes: Routes = [
  { path: '', component: BuscarTccComponent },
  { path: 'professores', component: ListarProfessoresComponent },
  { path: 'professores/:id', component: DetalheProfessorComponent },
  { path: ':id', component: DetalheTccComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PublicoRoutingModule {}
