import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { PainelService, PendingOrientationRequest } from '../../services/painel.service';

interface SolicitacaoOrientacaoView {
  id: string;
  nomeAluno: string;
  tituloDeTCC: string;
  tipo: string;
  prazoAceite: string | null;
}

@Component({
  selector: 'app-aceite-orientacao',
  templateUrl: './aceite-orientacao.component.html',
  styleUrls: ['./aceite-orientacao.component.css'],
})
export class AceiteOrientacaoComponent implements OnInit {
  solicitacoes: SolicitacaoOrientacaoView[] = [];
  expandedId: string | null = null;
  acaoAtual: 'ACEITAR' | 'REJEITAR' | null = null;
  solicitacaoAtiva: SolicitacaoOrientacaoView | null = null;
  nomeOrientador = '';

  isLoading = false;
  isConfirmando = false;
  errorMessage = '';
  successMessage = '';

  prazoAceite: Date | null = null;

  readonly acaoForm = this.fb.group({
    observacao: ['', [Validators.maxLength(1000)]],
    statusTCC: ['', Validators.required],
  });

  readonly statusOpcoes: Record<'ACEITAR' | 'REJEITAR', string[]> = {
    ACEITAR: ['Orientador Aceito - Em andamento'],
    REJEITAR: ['Recusado pelo Orientador'],
  };

  constructor(
    private readonly fb: FormBuilder,
    private readonly location: Location,
    private readonly painelService: PainelService,
  ) {}

  ngOnInit(): void {
    this.carregarDados();
  }

  get foraDoPrazo(): boolean {
    if (!this.prazoAceite) return false;
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    return hoje > this.prazoAceite;
  }

  get diasAtraso(): number {
    if (!this.prazoAceite) return 0;
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    return Math.ceil((hoje.getTime() - this.prazoAceite.getTime()) / (1000 * 60 * 60 * 24));
  }

  abrirAcao(solicitacao: SolicitacaoOrientacaoView, acao: 'ACEITAR' | 'REJEITAR'): void {
    if (this.expandedId === solicitacao.id && this.acaoAtual === acao) {
      this.fecharPainel();
      return;
    }

    this.expandedId = solicitacao.id;
    this.acaoAtual = acao;
    this.solicitacaoAtiva = solicitacao;
    this.errorMessage = '';
    this.successMessage = '';

    this.acaoForm.patchValue({
      observacao: '',
      statusTCC: this.statusOpcoes[acao][0],
    });
  }

  fecharPainel(): void {
    this.expandedId = null;
    this.acaoAtual = null;
    this.solicitacaoAtiva = null;
    this.acaoForm.reset();
  }

  confirmar(): void {
    this.acaoForm.markAllAsTouched();
    if (this.acaoForm.invalid || !this.solicitacaoAtiva || !this.acaoAtual || this.isConfirmando) return;

    const observacao = this.acaoForm.controls.observacao.getRawValue()?.trim() ?? '';
    if (this.acaoAtual === 'REJEITAR' && observacao.length === 0) {
      this.errorMessage = 'Informe uma observação para recusar a solicitação de orientação.';
      return;
    }

    this.isConfirmando = true;
    this.errorMessage = '';
    const acaoBackend = this.acaoAtual === 'REJEITAR' ? 'RECUSAR' : 'ACEITAR';

    this.painelService
      .decidirSolicitacaoOrientacao(this.solicitacaoAtiva.id, {
        acao: acaoBackend,
        ...(observacao ? { observacao } : {}),
      })
      .pipe(finalize(() => (this.isConfirmando = false)))
      .subscribe({
        next: (response) => {
          const acao = this.acaoAtual === 'ACEITAR' ? 'aceita' : 'recusada';
          this.successMessage = `Solicitação de ${response.aluno_nome} ${acao} com sucesso.`;
          if (response.alerta_acao_prazo) {
            this.successMessage = `${this.successMessage} ${response.alerta_acao_prazo}`;
          }
          this.solicitacoes = this.solicitacoes.filter((s) => s.id !== this.solicitacaoAtiva!.id);
          this.prazoAceite = this.resolvePrazoAceite(this.solicitacoes);
          this.fecharPainel();
        },
        error: (err: unknown) => {
          this.errorMessage = getApiErrorMessage(err, 'Não foi possível processar a solicitação.');
        },
      });
  }

  voltar(): void {
    this.location.back();
  }

  private carregarDados(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    forkJoin({
      user: this.painelService.getMeuPerfil(),
      solicitacoes: this.painelService.listarSolicitacoesOrientacaoPendentes(),
    })
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: ({ user, solicitacoes }) => {
          this.nomeOrientador = user.nome_completo;
          this.solicitacoes = solicitacoes.map((solicitacao) => this.mapSolicitacao(solicitacao));
          this.prazoAceite = this.resolvePrazoAceite(this.solicitacoes);
        },
        error: (err: unknown) => {
          this.errorMessage = getApiErrorMessage(err, 'Não foi possível carregar as solicitações.');
        },
      });
  }

  private mapSolicitacao(solicitacao: PendingOrientationRequest): SolicitacaoOrientacaoView {
    return {
      id: solicitacao.tcc_id,
      nomeAluno: solicitacao.aluno_nome,
      tituloDeTCC: solicitacao.titulo,
      tipo: solicitacao.tipo_tcc,
      prazoAceite: solicitacao.prazo_aceite,
    };
  }

  private resolvePrazoAceite(solicitacoes: SolicitacaoOrientacaoView[]): Date | null {
    const datas = solicitacoes
      .map((solicitacao) => solicitacao.prazoAceite)
      .filter((prazo): prazo is string => prazo !== null)
      .sort();

    if (datas.length === 0) {
      return null;
    }

    const [year, month, day] = datas[0].split('-').map(Number);
    return new Date(year, month - 1, day);
  }
}
