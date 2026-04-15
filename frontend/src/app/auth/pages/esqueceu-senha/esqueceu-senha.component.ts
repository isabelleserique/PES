import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-esqueceu-senha',
  templateUrl: './esqueceu-senha.component.html',
  styleUrls: ['./esqueceu-senha.component.css'],
})
export class EsqueceuSenhaComponent {
  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly router: Router,
    private readonly authService: AuthService,
  ) {}

  submit(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    this.authService.esqueceuSenha(this.form.getRawValue()).subscribe();
  }

  cancelar(): void {
    this.router.navigate(['/auth/login']);
  }
}
