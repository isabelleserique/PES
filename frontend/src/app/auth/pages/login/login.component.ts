import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';

import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
})
export class LoginComponent {
  readonly apiUrl = environment.apiUrl;

  readonly form = this.formBuilder.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    senha: ['', [Validators.required, Validators.minLength(8)]],
  });

  constructor(private readonly formBuilder: FormBuilder) {}

  submit(): void {
    this.form.markAllAsTouched();
  }
}
