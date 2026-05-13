import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin, of, throwError } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';

import { AuthService } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import {
  AuthenticatedUserProfile,
  CronogramaAluno,
  CronogramaPeriodoResponse,
  OrientadorDisponivel,
  PainelService,
  TccPayload,
  TccResponse,
  TipoTccAluno,
} from '../../services/painel.service';

@Component({
  selector: 'app-painel-aluno',
  templateUrl: './aluno.component.html',
  styleUrls: ['./aluno.component.css'],
})
export class PainelAlunoComponent implements OnInit {
  isLoading = true;
  isSavingTcc = false;
  errorMessage = '';
  feedbackMessage = '';
  currentUser: AuthenticatedUserProfile | null = null;
  cronograma: CronogramaPeriodoResponse | null = null;
  meuTcc: TccResponse | null = null;
  orientadores: OrientadorDisponivel[] = [];
  readonly tiposTcc: ReadonlyArray<{ value: TipoTccAluno; label: string }> = [
    { value: 'Artigo', label: 'Artigo Cientifico' },
    { value: 'Monografia', label: 'Monografia' },
    { value: 'Relatorio de Estagio', label: 'Relatorio de Estagio' },
  ];
  readonly tccForm = this.fb.nonNullable.group({
    titulo: ['', [Validators.required, Validators.minLength(3)]],
    tipo_tcc: ['Artigo' as TipoTccAluno, Validators.required],
    orientador_id: ['', Validators.required],
    coorientador_id: [''],
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly painelService: PainelService,
    private readonly router: Router,
  ) {
    this.tccForm.controls.orientador_id.valueChanges.subscribe((orientadorId) => {
      if (this.tccForm.controls.coorientador_id.getRawValue() === orientadorId) {
        this.tccForm.controls.coorientador_id.setValue('');
      }
    });
  }

  ngOnInit(): void {
    this.loadPainel();
  }

  get cronogramaAluno(): CronogramaAluno | null {
    return this.cronograma?.aluno ?? null;
  }

  get coorientadoresDisponiveis(): OrientadorDisponivel[] {
    const orientadorSelecionado = this.tccForm.controls.orientador_id.getRawValue();
    return this.orientadores.filter((orientador) => orientador.id !== orientadorSelecionado);
  }

  logout(): void {
    this.authService.clearSession();
    void this.router.navigate(['/auth/login']);
  }

  submitTcc(): void {
    this.tccForm.markAllAsTouched();
    if (this.tccForm.invalid || this.isSavingTcc) {
      return;
    }

    const alreadyHadTcc = this.meuTcc !== null;
    const rawValue = this.tccForm.getRawValue();
    const payload: TccPayload = {
      titulo: rawValue.titulo.trim(),
      tipo_tcc: rawValue.tipo_tcc,
      orientador_id: rawValue.orientador_id,
      ...(rawValue.coorientador_id ? { coorientador_id: rawValue.coorientador_id } : {}),
    };

    this.isSavingTcc = true;
    this.errorMessage = '';
    this.feedbackMessage = '';

    const request$ = alreadyHadTcc
      ? this.painelService.atualizarMeuTcc(payload)
      : this.painelService.criarMeuTcc(payload);

    request$
      .pipe(finalize(() => (this.isSavingTcc = false)))
      .subscribe({
        next: (response) => {
          this.meuTcc = response;
          this.syncFormWithTcc(response);
          this.reloadCronograma();
          this.feedbackMessage = alreadyHadTcc
            ? 'Dados do TCC atualizados com sucesso.'
            : 'TCC registrado com sucesso.';
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel salvar os dados do TCC.');
        },
      });
  }

  private loadPainel(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.feedbackMessage = '';

    forkJoin({
      user: this.painelService.getMeuPerfil(),
      cronograma: this.painelService.getCronogramaAtivo(),
      orientadores: this.painelService.listarOrientadoresDisponiveis(),
      tcc: this.painelService.getMeuTcc().pipe(
        catchError((error: unknown) => (this.isNotFound(error) ? of(null) : throwError(() => error))),
      ),
    })
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: ({ user, cronograma, orientadores, tcc }) => {
          this.currentUser = user;
          this.cronograma = cronograma;
          this.orientadores = orientadores;
          this.meuTcc = tcc;
          this.syncFormWithTcc(tcc);
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel carregar o painel do aluno.');
        },
      });
  }

  private reloadCronograma(): void {
    this.painelService.getCronogramaAtivo().subscribe({
      next: (cronograma) => {
        this.cronograma = cronograma;
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel atualizar o cronograma.');
      },
    });
  }

  private syncFormWithTcc(tcc: TccResponse | null): void {
    if (tcc === null) {
      this.tccForm.reset({
        titulo: '',
        tipo_tcc: 'Artigo',
        orientador_id: '',
        coorientador_id: '',
      });
      return;
    }

    this.tccForm.reset({
      titulo: tcc.titulo,
      tipo_tcc: tcc.tipo_tcc,
      orientador_id: tcc.orientador_id,
      coorientador_id: tcc.coorientador_id ?? '',
    });
  }

  private isNotFound(error: unknown): boolean {
    return (
      typeof error === 'object'
      && error !== null
      && 'status' in error
      && (error as { status?: unknown }).status === 404
    );
  }
}
