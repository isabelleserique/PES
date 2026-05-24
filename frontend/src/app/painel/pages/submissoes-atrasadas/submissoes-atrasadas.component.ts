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

  constructor(
    private readonly submissaoService: SubmissaoService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.submissaoService
      .listarSubmissoesAtrasadas()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (submissoes) => {
          this.submissoes = submissoes;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel carregar as submissoes atrasadas.');
        },
      });
  }

  get submissoesFiltradas(): SubmissaoAtrasada[] {
    if (!this.filtroTipo) return this.submissoes;
    return this.submissoes.filter((s) => s.tipo_tcc === this.filtroTipo);
  }

  get tiposDisponiveis(): string[] {
    return [...new Set(this.submissoes.map((s) => s.tipo_tcc))];
  }

  get totalDiasAtraso(): number {
    return this.submissoesFiltradas.reduce((acc, s) => acc + s.dias_atraso, 0);
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

  formatarDataCurta(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('pt-BR');
  }
}
