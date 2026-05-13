import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { SubmissaoHistorico, SubmissaoService } from '../../services/submissao.service';

@Component({
  selector: 'app-historico-submissoes',
  templateUrl: './historico-submissoes.component.html',
  styleUrls: ['./historico-submissoes.component.css'],
})
export class HistoricoSubmissoesComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  historico: SubmissaoHistorico[] = [];

  filtroTipo = '';
  filtroForaDoPrazo = false;

  constructor(
    private readonly submissaoService: SubmissaoService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.submissaoService.listarHistoricoSubmissoes().subscribe({
      next: (data) => {
        this.historico = data;
        this.isLoading = false;
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar o histórico.');
        this.isLoading = false;
      },
    });
  }

  get historicoFiltrado(): SubmissaoHistorico[] {
    return this.historico.filter((s) => {
      if (this.filtroTipo && s.tipo_tcc !== this.filtroTipo) return false;
      if (this.filtroForaDoPrazo && !s.fora_do_prazo) return false;
      return true;
    });
  }

  get tiposDisponiveis(): string[] {
    return [...new Set(this.historico.map((s) => s.tipo_tcc))];
  }

  voltar(): void {
    void this.router.navigate(['/painel/coordenador']);
  }

  formatarData(dateStr: string): string {
    return new Date(dateStr).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
