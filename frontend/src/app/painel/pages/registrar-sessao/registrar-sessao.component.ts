import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { AuthService } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import {
  CronogramaOrientando,
  PainelService,
  SessaoOrientacao,
  SessaoOrientacaoPayload,
} from '../../services/painel.service';

@Component({
  selector: 'app-registrar-sessao',
  templateUrl: './registrar-sessao.component.html',
  styleUrls: ['./registrar-sessao.component.css'],
})
export class RegistrarSessaoComponent implements OnInit {
  isLoading = true;
  isSaving = false;
  isLoadingSessoes = false;
  errorMessage = '';
  feedbackMessage = '';
  orientandos: CronogramaOrientando[] = [];
  sessoes: SessaoOrientacao[] = [];
  orientandoSelecionado: CronogramaOrientando | null = null;

  readonly sessaoForm = this.fb.group({
    aluno_id: ['', Validators.required],
    data_sessao: [null as Date | null, Validators.required],
    resumo: ['', [Validators.required, Validators.minLength(10)]],
    proximos_passos: ['', [Validators.required, Validators.minLength(10)]],
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly painelService: PainelService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadOrientandos();
    this.sessaoForm.controls.aluno_id.valueChanges.subscribe((alunoId) => {
      this.orientandoSelecionado = this.orientandos.find((orientando) => orientando.aluno_id === alunoId) ?? null;
      this.feedbackMessage = '';
      this.errorMessage = '';
      if (alunoId) {
        this.carregarSessoes(alunoId);
      } else {
        this.sessoes = [];
      }
    });
  }

  logout(): void {
    this.authService.clearSession();
    void this.router.navigate(['/auth/login']);
  }

  registrarSessao(): void {
    this.sessaoForm.markAllAsTouched();
    if (this.sessaoForm.invalid || this.isSaving) {
      return;
    }

    const rawValue = this.sessaoForm.getRawValue();
    const dataSessao = rawValue.data_sessao as Date;
    const payload: SessaoOrientacaoPayload = {
      aluno_id: rawValue.aluno_id ?? '',
      data_sessao: this.formatDateInput(dataSessao),
      resumo: (rawValue.resumo ?? '').trim(),
      proximos_passos: (rawValue.proximos_passos ?? '').trim(),
    };

    this.isSaving = true;
    this.errorMessage = '';
    this.feedbackMessage = '';

    this.painelService
      .registrarSessaoOrientacao(payload)
      .pipe(finalize(() => (this.isSaving = false)))
      .subscribe({
        next: (sessao) => {
          this.sessoes = [sessao, ...this.sessoes];
          this.sessaoForm.patchValue({
            data_sessao: null,
            resumo: '',
            proximos_passos: '',
          });
          this.sessaoForm.controls.data_sessao.markAsUntouched();
          this.sessaoForm.controls.resumo.markAsUntouched();
          this.sessaoForm.controls.proximos_passos.markAsUntouched();
          this.feedbackMessage = 'Sessão de orientação registrada com sucesso.';
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível registrar a sessão de orientação.');
        },
      });
  }

  private loadOrientandos(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.painelService
      .getCronogramaAtivo()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (cronograma) => {
          this.orientandos = cronograma.orientandos ?? [];
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar os orientandos.');
        },
      });
  }

  private carregarSessoes(alunoId: string): void {
    this.isLoadingSessoes = true;
    this.sessoes = [];

    this.painelService
      .listarSessoesOrientador(alunoId)
      .pipe(finalize(() => (this.isLoadingSessoes = false)))
      .subscribe({
        next: (sessoes) => {
          this.sessoes = sessoes;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar as sessões de orientação.');
        },
      });
  }

  private formatDateInput(date: Date): string {
    return [
      date.getFullYear(),
      String(date.getMonth() + 1).padStart(2, '0'),
      String(date.getDate()).padStart(2, '0'),
    ].join('-');
  }
}
