import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { DepositoResponse, DepositoService, StatusDeposito } from '../../services/deposito.service';

interface EtapaStatus {
  status: StatusDeposito;
  label: string;
  descricao: string;
  icone: string;
}

@Component({
  selector: 'app-status-deposito',
  templateUrl: './status-deposito.component.html',
  styleUrls: ['./status-deposito.component.css'],
})
export class StatusDepositoComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  deposito: DepositoResponse | null = null;

  // Fluxo principal (sequencial). DEVOLVIDO_CORRECAO é tratado como estado de alerta à parte.
  readonly etapas: EtapaStatus[] = [
    { status: 'AGUARDANDO_ENVIO', label: 'Aguardando envio', descricao: 'O aluno ainda não enviou a versão final e os documentos.', icone: 'schedule' },
    { status: 'EM_REVISAO', label: 'Em revisão', descricao: 'A biblioteca está conferindo os arquivos enviados.', icone: 'fact_check' },
    { status: 'APROVADO', label: 'Aprovado', descricao: 'A documentação foi validada pela biblioteca.', icone: 'verified' },
    { status: 'DEPOSITADO', label: 'Depositado', descricao: 'O TCC foi oficialmente depositado no acervo.', icone: 'inventory_2' },
  ];

  constructor(
    private readonly location: Location,
    private readonly depositoService: DepositoService,
  ) {}

  ngOnInit(): void {
    this.carregar();
  }

  readonly statusLabels: Record<StatusDeposito, string> = {
    AGUARDANDO_ENVIO: 'Aguardando envio',
    EM_REVISAO: 'Em revisão',
    DEVOLVIDO_CORRECAO: 'Devolvido para correção',
    APROVADO: 'Aprovado',
    DEPOSITADO: 'Depositado',
  };

  get statusAtual(): StatusDeposito {
    return this.deposito?.status ?? 'AGUARDANDO_ENVIO';
  }

  get statusAtualLabel(): string {
    return this.statusLabels[this.statusAtual];
  }

  get foiDevolvido(): boolean {
    return this.statusAtual === 'DEVOLVIDO_CORRECAO';
  }

  estadoDaEtapa(etapa: EtapaStatus): 'concluida' | 'atual' | 'pendente' {
    const ordem = this.etapas.findIndex((e) => e.status === etapa.status);
    const atual = this.foiDevolvido
      ? this.etapas.findIndex((e) => e.status === 'EM_REVISAO')
      : this.etapas.findIndex((e) => e.status === this.statusAtual);

    if (atual < 0) return 'pendente';
    if (ordem < atual) return 'concluida';
    if (ordem === atual) return 'atual';
    return 'pendente';
  }

  voltar(): void {
    this.location.back();
  }

  private carregar(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.depositoService
      .getMeuDeposito()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (deposito) => {
          this.deposito = deposito;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar o status do depósito.');
        },
      });
  }
}
