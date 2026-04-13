import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { CadastroComponent } from './pages/cadastro/cadastro.component';
import { EsqueceuSenhaComponent } from './pages/esqueceu-senha/esqueceu-senha.component';
import { LoginComponent } from './pages/login/login.component';
import { RedefinirSenhaComponent } from './pages/redefinir-senha/redefinir-senha.component';

const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'cadastro', component: CadastroComponent },
  { path: 'esqueceu-senha', component: EsqueceuSenhaComponent },
  { path: 'redefinir-senha', component: RedefinirSenhaComponent },
  { path: '', pathMatch: 'full', redirectTo: 'login' },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AuthRoutingModule {}
