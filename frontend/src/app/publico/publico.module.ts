import { NgModule } from '@angular/core';

import { SharedModule } from '../shared/shared.module';
import { BuscarTccComponent } from './pages/buscar-tcc/buscar-tcc.component';
import { DetalheTccComponent } from './pages/detalhe-tcc/detalhe-tcc.component';
import { ListarProfessoresComponent } from './pages/listar-professores/listar-professores.component';
import { DetalheProfessorComponent } from './pages/detalhe-professor/detalhe-professor.component';
import { PublicoRoutingModule } from './publico-routing.module';

@NgModule({
  declarations: [
    BuscarTccComponent,
    DetalheTccComponent,
    ListarProfessoresComponent,
    DetalheProfessorComponent,
  ],
  imports: [SharedModule, PublicoRoutingModule],
})
export class PublicoModule {}
