import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { PainelService } from '../../services/painel.service';
import { OrientadorService, SolicitacaoOrientacao } from '../../services/orientador.service';

@Component({
  selector: 'app-aceite-orientacao',
  templateUrl: './aceite-orientacao.component.html',
  styleUrls: ['./aceite-orientacao.component.css'],
})
export class AceiteOrientacaoComponent implements OnInit {
  solicitacoes: SolicitacaoOrientacao[] = [];
  expandedId: string | null = null;
  acaoAtual: 'ACEITAR' | 'REJEITAR' | null = null;
  solicitacaoAtiva: SolicitacaoOrientacao | null = null;
  nomeOrientador = '';

  isLoading = false;
  isConfirmando = false;
  errorMessage = '';
  successMessage = '';

  prazoAceite: Date | null = null;

  readonly acaoForm = this.fb.group({
    observacao: [''],
    statusTCC: ['', Validators.required],
  });

  readonly statusOpcoes: Record<'ACEITAR' | 'REJEITAR', string[]> = {
    ACEITAR: ['Orientador Aceito - Em andamento'],
    REJEITAR: ['Recusado pelo Orientador'],
  };

  constructor(
    private readonly fb: FormBuilder,
    private readonly painelService: PainelService,
    private readonly orientadorService: OrientadorService,
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

  abrirAcao(solicitacao: SolicitacaoOrientacao, acao: 'ACEITAR' | 'REJEITAR'): void {
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

    this.isConfirmando = true;
    this.errorMessage = '';

    const { observacao, statusTCC } = this.acaoForm.getRawValue();

    this.orientadorService
      .responderSolicitacao(this.solicitacaoAtiva.id, {
        acao: this.acaoAtual,
        observacao: observacao ?? '',
        status_tcc: statusTCC!,
      })
      .pipe(finalize(() => (this.isConfirmando = false)))
      .subscribe({
        next: () => {
          const nome = this.solicitacaoAtiva!.nomeAluno;
          const acao = this.acaoAtual === 'ACEITAR' ? 'aceita' : 'recusada';
          this.successMessage = `Solicitação de ${nome} ${acao} com sucesso. O aluno será notificado.`;
          this.solicitacoes = this.solicitacoes.filter((s) => s.id !== this.solicitacaoAtiva!.id);
          this.fecharPainel();
        },
        error: (err: unknown) => {
          this.errorMessage = getApiErrorMessage(err, 'Não foi possível processar a solicitação.');
        },
      });
  }

  private carregarDados(): void {
    this.isLoading = true;

    this.painelService
      .getMeuPerfil()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (user) => {
          this.nomeOrientador = user.nome_completo;
          this.carregarSolicitacoes();
        },
        error: (err: unknown) => {
          this.errorMessage = getApiErrorMessage(err, 'Não foi possível carregar seus dados.');
        },
      });
  }

  private carregarSolicitacoes(): void {
    this.orientadorService.listarSolicitacoes().subscribe({
      next: (lista) => (this.solicitacoes = lista),
      error: (err: unknown) => {
        this.errorMessage = getApiErrorMessage(err, 'Não foi possível carregar as solicitações.');
      },
    });
  }
}
