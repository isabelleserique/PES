import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { AuthService } from '../../services/auth.service';
import { getApiErrorMessage } from '../../utils/api-error.util';

@Component({
  selector: 'app-esqueceu-senha',
  templateUrl: './esqueceu-senha.component.html',
  styleUrls: ['./esqueceu-senha.component.css'],
})
export class EsqueceuSenhaComponent {
  isSubmitting = false;
  errorMessage = '';
  successMessage = '';

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
    if (this.form.invalid || this.isSubmitting) {
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.authService
      .esqueceuSenha(this.form.getRawValue())
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: (response) => {
          this.successMessage = response.mensagem;
          this.form.reset({ email: '' });
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel solicitar a redefinicao de senha.');
        },
      });
  }

  cancelar(): void {
    this.router.navigate(['/auth/login']);
  }
}
