import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-redefinir-senha',
  templateUrl: './redefinir-senha.component.html',
  styleUrls: ['./redefinir-senha.component.css'],
})
export class RedefinirSenhaComponent {
  readonly form = this.fb.nonNullable.group({
    nova_senha: ['', [Validators.required, Validators.minLength(8)]],
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
    this.authService.redefinirSenha(this.form.getRawValue()).subscribe();
  }

  cancelar(): void {
    this.router.navigate(['/auth/login']);
  }
}
