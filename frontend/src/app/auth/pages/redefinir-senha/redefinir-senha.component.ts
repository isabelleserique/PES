import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { AuthService } from '../../services/auth.service';
import { getApiErrorMessage } from '../../utils/api-error.util';
import { passwordMatchValidator } from '../../utils/form-validators.util';

@Component({
  selector: 'app-redefinir-senha',
  templateUrl: './redefinir-senha.component.html',
  styleUrls: ['./redefinir-senha.component.css'],
})
export class RedefinirSenhaComponent {
  isSubmitting = false;
  errorMessage = '';
  successMessage = '';
  readonly token: string;

  readonly form = this.fb.nonNullable.group({
    nova_senha: ['', [Validators.required, Validators.minLength(8)]],
    confirmar_senha: ['', Validators.required],
  }, {
    validators: passwordMatchValidator('nova_senha', 'confirmar_senha'),
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly authService: AuthService,
  ) {
    this.token = this.route.snapshot.queryParamMap.get('token')?.trim() ?? '';
    if (!this.token) {
      this.errorMessage = 'O link de redefinicao de senha esta invalido ou incompleto.';
    }
  }

  submit(): void {
    this.form.markAllAsTouched();
    if (!this.token) {
      this.errorMessage = 'O link de redefinicao de senha esta invalido ou incompleto.';
      return;
    }
    if (this.form.invalid || this.isSubmitting) {
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.authService
      .redefinirSenha({
        token: this.token,
        nova_senha: this.form.controls.nova_senha.getRawValue(),
      })
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: (response) => {
          this.successMessage = response.mensagem;
          this.form.reset({
            nova_senha: '',
            confirmar_senha: '',
          });
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel redefinir a senha.');
        },
      });
  }

  cancelar(): void {
    this.router.navigate(['/auth/login']);
  }
}
