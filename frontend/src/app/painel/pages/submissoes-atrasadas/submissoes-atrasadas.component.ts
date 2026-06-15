import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { SubmissaoAtrasada, SubmissaoService } from '../../services/submissao.service';

@Component({
  selector: 'app-submissoes-atrasadas',
  templateUrl: './submissoes-atrasadas.component.html',
  styleUrls: ['./submissoes-atrasadas.component.css'],
})
export class SubmissoesAtrasadasComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  submissoes: SubmissaoAtrasada[] = [];
  filtroTipo = '';
  arquivoEmVisualizacaoId: string | null = null;

  constructor(
    private readonly submissaoService: SubmissaoService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadSubmissoes();
  }

  get submissoesFiltradas(): SubmissaoAtrasada[] {
    return this.filtroTipo
      ? this.submissoes.filter((submissao) => submissao.tipo_tcc === this.filtroTipo)
      : this.submissoes;
  }

  get tiposDisponiveis(): string[] {
    return [...new Set(this.submissoes.map((submissao) => submissao.tipo_tcc))].sort();
  }

  get totalDiasAtraso(): number {
    return this.submissoesFiltradas.reduce((total, submissao) => total + submissao.dias_atraso, 0);
  }

  voltar(): void {
    void this.router.navigate(['/painel/coordenador']);
  }

  visualizarArquivo(submissao: SubmissaoAtrasada): void {
    if (this.arquivoEmVisualizacaoId) {
      return;
    }

    this.arquivoEmVisualizacaoId = submissao.id;
    this.submissaoService
      .visualizarArquivo(submissao.id)
      .pipe(finalize(() => (this.arquivoEmVisualizacaoId = null)))
      .subscribe({
        next: (blob) => {
          const url = URL.createObjectURL(blob);
          window.open(url, '_blank', 'noopener');
          setTimeout(() => URL.revokeObjectURL(url), 30_000);
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível abrir o arquivo.');
        },
      });
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

  formatarDataCurta(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('pt-BR');
  }

  private loadSubmissoes(): void {
    this.submissaoService
      .listarSubmissoesAtrasadas()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (submissoes) => {
          this.submissoes = submissoes;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar as submissões atrasadas.');
        },
      });
  }
}
