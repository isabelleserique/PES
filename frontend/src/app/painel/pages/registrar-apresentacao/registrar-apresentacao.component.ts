import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';

import { AuthService } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { PainelService, TccResponse } from '../../services/painel.service';
import {
  ApresentacaoArtigo,
  ApresentacaoArtigoPayload,
  SubmissaoService,
} from '../../services/submissao.service';

@Component({
  selector: 'app-registrar-apresentacao',
  templateUrl: './registrar-apresentacao.component.html',
  styleUrls: ['./registrar-apresentacao.component.css'],
})
export class RegistrarApresentacaoComponent implements OnInit {
  isLoading = true;
  isSaving = false;
  errorMessage = '';
  feedbackMessage = '';
  meuTcc: TccResponse | null = null;
  apresentacoes: ApresentacaoArtigo[] = [];
  artigoJaAceito = false;

  readonly apresentacaoForm = this.fb.group({
    data_apresentacao: [null as Date | null, Validators.required],
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly painelService: PainelService,
    private readonly submissaoService: SubmissaoService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadDados();
  }

  get isArtigo(): boolean {
    return this.meuTcc?.tipo_tcc === 'Artigo';
  }

  logout(): void {
    this.authService.clearSession();
    void this.router.navigate(['/auth/login']);
  }

  registrarApresentacao(): void {
    this.apresentacaoForm.markAllAsTouched();
    if (this.apresentacaoForm.invalid || this.isSaving) {
      return;
    }

    const dataApresentacao = this.apresentacaoForm.controls.data_apresentacao.value as Date;
    const payload: ApresentacaoArtigoPayload = {
      data_apresentacao: this.formatDateInput(dataApresentacao),
    };

    this.isSaving = true;
    this.errorMessage = '';
    this.feedbackMessage = '';

    this.submissaoService
      .registrarApresentacaoArtigo(payload)
      .pipe(finalize(() => (this.isSaving = false)))
      .subscribe({
        next: (apresentacao) => {
          this.apresentacoes = [apresentacao, ...this.apresentacoes];
          this.artigoJaAceito = this.artigoJaAceito || apresentacao.artigo_ja_aceito;
          this.apresentacaoForm.reset({ data_apresentacao: null });
          this.feedbackMessage = apresentacao.artigo_ja_aceito
            ? 'Apresentação registrada. Como o artigo já possui aceite comprovado, esta etapa não impacta a nota.'
            : 'Apresentação registrada com sucesso.';
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível registrar a apresentação.');
        },
      });
  }

  private loadDados(): void {
    this.isLoading = true;

    forkJoin({
      tcc: this.painelService.getMeuTcc().pipe(catchError(() => of(null))),
      apresentacoes: this.submissaoService.listarMinhasApresentacoes().pipe(catchError(() => of([]))),
      historico: this.submissaoService.listarSubmissoesEntregaveis().pipe(catchError(() => of([]))),
    })
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: ({ tcc, apresentacoes, historico }) => {
          this.meuTcc = tcc;
          this.apresentacoes = apresentacoes;
          this.artigoJaAceito = historico.some((submissao) => submissao.foi_aceito);
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar os dados.');
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
