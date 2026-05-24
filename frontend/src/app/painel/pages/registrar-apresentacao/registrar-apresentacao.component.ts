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

    const dataObj = this.apresentacaoForm.controls.data_apresentacao.value as Date;
    const dataFormatada = `${dataObj.getFullYear()}-${String(dataObj.getMonth() + 1).padStart(2, '0')}-${String(dataObj.getDate()).padStart(2, '0')}`;

    const payload: ApresentacaoArtigoPayload = { data_apresentacao: dataFormatada };

    this.isSaving = true;
    this.errorMessage = '';
    this.feedbackMessage = '';

    this.submissaoService
      .registrarApresentacaoArtigo(payload)
      .pipe(finalize(() => (this.isSaving = false)))
      .subscribe({
        next: (apresentacao) => {
          this.apresentacoes = [apresentacao, ...this.apresentacoes];
          this.apresentacaoForm.reset({ data_apresentacao: null });
          this.feedbackMessage = 'Apresentacao registrada com sucesso.';
          if (apresentacao.artigo_ja_aceito) {
            this.feedbackMessage += ' Como o artigo ja possui aceite comprovado, esta etapa nao impacta a nota.';
          }
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel registrar a apresentacao.');
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
          this.artigoJaAceito = historico.some((s) => s.foi_aceito);
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel carregar os dados.');
        },
      });
  }
}
