import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';

import { AuthRoutingModule } from './auth-routing.module';
import { CadastroComponent } from './pages/cadastro/cadastro.component';
import { EsqueceuSenhaComponent } from './pages/esqueceu-senha/esqueceu-senha.component';
import { LoginComponent } from './pages/login/login.component';
import { RedefinirSenhaComponent } from './pages/redefinir-senha/redefinir-senha.component';
import { SharedModule } from '../shared/shared.module';

@NgModule({
  declarations: [LoginComponent, CadastroComponent, EsqueceuSenhaComponent, RedefinirSenhaComponent],
  imports: [CommonModule, ReactiveFormsModule, SharedModule, AuthRoutingModule],
})
export class AuthModule {}
