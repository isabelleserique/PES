import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { finalize } from 'rxjs/operators';

import { AuthService, CadastroPayload, CadastroPerfil } from '../../services/auth.service';
import { getApiErrorMessage } from '../../utils/api-error.util';
import { passwordMatchValidator } from '../../utils/form-validators.util';

@Component({
  selector: 'app-cadastro',
  templateUrl: './cadastro.component.html',
  styleUrls: ['./cadastro.component.css'],
})
export class CadastroComponent {
  isSubmitting = false;
  errorMessage = '';
  successMessage = '';

  readonly form = this.fb.nonNullable.group({
    perfil: ['ALUNO' as CadastroPerfil, Validators.required],
    nome_completo: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    username: ['', Validators.required],
    matricula: [''],
    senha: ['', [Validators.required, Validators.minLength(8)]],
    confirmar_senha: ['', Validators.required],
  }, {
    validators: passwordMatchValidator('senha', 'confirmar_senha'),
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
  ) {
    this.updateMatriculaValidators(this.form.controls.perfil.getRawValue());
    this.form.controls.perfil.valueChanges.subscribe((perfil) => this.updateMatriculaValidators(perfil));
  }

  get isAlunoSelected(): boolean {
    return this.form.controls.perfil.getRawValue() === 'ALUNO';
  }

  submit(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid || this.isSubmitting) {
      return;
    }

    const rawValue = this.form.getRawValue();
    const payload: CadastroPayload = {
      perfil: rawValue.perfil,
      nome_completo: rawValue.nome_completo.trim(),
      email: rawValue.email.trim(),
      username: rawValue.username.trim(),
      senha: rawValue.senha,
      ...(rawValue.perfil === 'ALUNO' ? { matricula: rawValue.matricula.trim() } : {}),
    };

    this.isSubmitting = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.authService
      .cadastrar(payload)
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: (response) => {
          this.successMessage = response.mensagem;
          this.form.reset({
            perfil: 'ALUNO',
            nome_completo: '',
            email: '',
            username: '',
            matricula: '',
            senha: '',
            confirmar_senha: '',
          });
          this.updateMatriculaValidators('ALUNO');
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel enviar a solicitacao de cadastro.');
        },
      });
  }

  private updateMatriculaValidators(perfil: CadastroPerfil): void {
    const matriculaControl = this.form.controls.matricula;

    if (perfil === 'ALUNO') {
      matriculaControl.setValidators([Validators.required]);
    } else {
      matriculaControl.clearValidators();
      matriculaControl.setValue('');
    }

    matriculaControl.updateValueAndValidity({ emitEvent: false });
  }
}
