import { NgModule } from '@angular/core';

import { SharedModule } from '../shared/shared.module';
import { PainelAlunoComponent } from './pages/aluno/aluno.component';
import { PainelCoordenadorComponent } from './pages/painel/painel.component';
import { PainelRedirectComponent } from './pages/redirect/redirect.component';
import { PainelOrientadorComponent } from './pages/orientador/orientador.component';
import { PainelRoutingModule } from './painel-routing.module';

@NgModule({
  declarations: [
    PainelCoordenadorComponent,
    PainelAlunoComponent,
    PainelOrientadorComponent,
    PainelRedirectComponent,
  ],
  imports: [SharedModule, PainelRoutingModule],
})
export class PainelModule {}
