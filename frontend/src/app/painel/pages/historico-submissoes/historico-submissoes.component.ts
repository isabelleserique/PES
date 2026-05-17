import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';

import { AuthService, UserPerfil } from '../../../auth/services/auth.service';
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
  readonly perfil: UserPerfil | null;

  constructor(
    private readonly authService: AuthService,
    private readonly submissaoService: SubmissaoService,
    private readonly router: Router,
  ) {
    this.perfil = this.authService.getStoredPerfil();
  }

  ngOnInit(): void {
    this.getHistoricoRequest().subscribe({
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
    return this.historico.filter((submissao) => {
      if (this.filtroTipo && submissao.tipo_tcc !== this.filtroTipo) return false;
      if (this.filtroForaDoPrazo && !submissao.fora_do_prazo) return false;
      return true;
    });
  }

  get tiposDisponiveis(): string[] {
    return Array.from(new Set(this.historico.map((submissao) => submissao.tipo_tcc)));
  }

  get homeRoute(): string[] {
    return this.authService.getPostLoginRoute();
  }

  get pageScopeLabel(): string {
    return this.perfil === 'ORIENTADOR' ? 'US016 - Orientador' : 'US016 - Coordenador';
  }

  get pageSubtitle(): string {
    return this.perfil === 'ORIENTADOR'
      ? 'Visualize as versões enviadas pelos seus orientandos. Nenhum arquivo pode ser excluído.'
      : 'Visualize todas as versões enviadas pelos alunos. Nenhum arquivo pode ser excluído.';
  }

  voltar(): void {
    void this.router.navigate(this.homeRoute);
  }

  visualizarArquivo(submissao: SubmissaoHistorico): void {
    this.abrirArquivo(this.submissaoService.visualizarArquivo(submissao.id));
  }

  visualizarComprovante(submissao: SubmissaoHistorico): void {
    this.abrirArquivo(this.submissaoService.visualizarComprovante(submissao.id));
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

  private getHistoricoRequest(): Observable<SubmissaoHistorico[]> {
    if (this.perfil === 'ORIENTADOR') {
      return this.submissaoService.listarHistoricoOrientador();
    }
    return this.submissaoService.listarHistoricoSubmissoes();
  }

  private abrirArquivo(request: Observable<Blob>): void {
    this.errorMessage = '';
    request.subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank', 'noopener');
        window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Não foi possível abrir o arquivo.');
      },
    });
  }
}
