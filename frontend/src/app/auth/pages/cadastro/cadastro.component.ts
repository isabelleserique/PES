import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-cadastro',
  templateUrl: './cadastro.component.html',
  styleUrls: ['./cadastro.component.css'],
})
export class CadastroComponent {
  readonly form = this.fb.nonNullable.group({
    perfil: ['ALUNO', Validators.required],
    nome_completo: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    username: ['', Validators.required],
    senha: ['', [Validators.required, Validators.minLength(8)]],
    confirmar_senha: ['', Validators.required],
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly router: Router,
    private readonly authService: AuthService,
  ) {}

  submit(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    const { confirmar_senha, ...payload } = this.form.getRawValue();
    this.authService.cadastrar(payload).subscribe();
  }
}
