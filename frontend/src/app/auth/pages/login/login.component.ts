import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { AuthService } from '../../services/auth.service';
import { getApiErrorMessage } from '../../utils/api-error.util';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
})
export class LoginComponent {
  isSubmitting = false;
  errorMessage = '';
  successMessage = '';

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    senha: ['', Validators.required],
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly router: Router,
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
      .login(this.form.getRawValue())
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: () => {
          void this.router.navigate(this.authService.getPostLoginRoute());
        },
        error: (error: unknown) => {
          this.authService.clearSession();
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel realizar o login.');
        },
      });
  }
}
