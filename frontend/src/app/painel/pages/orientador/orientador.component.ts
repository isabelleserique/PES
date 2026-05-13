import { Component, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { AuthService } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import {
  AuthenticatedUserProfile,
  CronogramaOrientando,
  CronogramaPeriodoResponse,
  OrientationDecisionPayload,
  PainelService,
  PendingOrientationRequest,
} from '../../services/painel.service';

@Component({
  selector: 'app-painel-orientador',
  templateUrl: './orientador.component.html',
  styleUrls: ['./orientador.component.css'],
})
export class PainelOrientadorComponent implements OnInit {
  isLoading = true;
  isReviewing = false;
  errorMessage = '';
  feedbackMessage = '';
  currentUser: AuthenticatedUserProfile | null = null;
  cronograma: CronogramaPeriodoResponse | null = null;
  pendingRequests: PendingOrientationRequest[] = [];
  observacoes: Record<string, string> = {};
  readonly filtroForm = this.fb.nonNullable.group({
    orientando_id: [''],
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly painelService: PainelService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadPainel();
  }

  get orientandosVisiveis(): CronogramaOrientando[] {
    const orientandoId = this.filtroForm.controls.orientando_id.getRawValue();
    const orientandos = this.cronograma?.orientandos ?? [];
    return orientandoId ? orientandos.filter((orientando) => orientando.aluno_id === orientandoId) : orientandos;
  }

  get hasPendingRequests(): boolean {
    return this.pendingRequests.length > 0;
  }

  logout(): void {
    this.authService.clearSession();
    void this.router.navigate(['/auth/login']);
  }

  updateObservacao(tccId: string, value: string): void {
    this.observacoes[tccId] = value;
  }

  decidirSolicitacao(request: PendingOrientationRequest, acao: OrientationDecisionPayload['acao']): void {
    if (this.isReviewing) {
      return;
    }

    const observacao = (this.observacoes[request.tcc_id] ?? '').trim();
    if (acao === 'RECUSAR' && observacao.length === 0) {
      this.errorMessage = 'Informe uma observacao ao recusar a solicitacao de orientacao.';
      this.feedbackMessage = '';
      return;
    }

    this.isReviewing = true;
    this.errorMessage = '';
    this.feedbackMessage = '';

    const payload: OrientationDecisionPayload = {
      acao,
      ...(observacao ? { observacao } : {}),
    };

    this.painelService
      .decidirSolicitacaoOrientacao(request.tcc_id, payload)
      .pipe(finalize(() => (this.isReviewing = false)))
      .subscribe({
        next: (response) => {
          this.pendingRequests = this.pendingRequests.filter((item) => item.tcc_id !== request.tcc_id);
          delete this.observacoes[request.tcc_id];
          this.feedbackMessage =
            acao === 'ACEITAR'
              ? `Orientacao de ${response.aluno_nome} aceita com sucesso.`
              : `Solicitacao de ${response.aluno_nome} recusada com sucesso.`;
          if (response.alerta_acao_prazo) {
            this.feedbackMessage = `${this.feedbackMessage} ${response.alerta_acao_prazo}`;
          }
          this.reloadCronograma();
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel registrar a decisao de orientacao.');
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
      pendingRequests: this.painelService.listarSolicitacoesOrientacaoPendentes(),
    })
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: ({ user, cronograma, pendingRequests }) => {
          this.currentUser = user;
          this.cronograma = cronograma;
          this.pendingRequests = pendingRequests;
          this.observacoes = {};
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel carregar o painel do orientador.');
        },
      });
  }

  private reloadCronograma(): void {
    this.painelService.getCronogramaAtivo().subscribe({
      next: (cronograma) => {
        this.cronograma = cronograma;
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel atualizar o cronograma do orientador.');
      },
    });
  }
}
