import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { LogAtividade, SubmissaoService } from '../../services/submissao.service';

@Component({
  selector: 'app-logs-sistema',
  templateUrl: './logs-sistema.component.html',
  styleUrls: ['./logs-sistema.component.css'],
})
export class LogsSistemaComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  logs: LogAtividade[] = [];
  filtroUsuario = '';
  filtroAcao = '';

  constructor(
    private readonly submissaoService: SubmissaoService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.submissaoService
      .listarLogsAtividade()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (logs) => {
          this.logs = logs;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar os logs do sistema.');
        },
      });
  }

  get logsFiltrados(): LogAtividade[] {
    return this.logs.filter((log) => {
      const usuarioMatch = this.filtroUsuario
        ? log.usuario_nome.toLowerCase().includes(this.filtroUsuario.toLowerCase())
        : true;
      const acaoMatch = this.filtroAcao ? log.acao === this.filtroAcao : true;
      return usuarioMatch && acaoMatch;
    });
  }

  get acoesDisponiveis(): string[] {
    return [...new Set(this.logs.map((log) => log.acao))].sort();
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
      second: '2-digit',
    });
  }
}
