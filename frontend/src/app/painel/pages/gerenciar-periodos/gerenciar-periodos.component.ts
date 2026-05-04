import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { PeriodoResponse, PeriodoService } from '../../services/periodo.service';

@Component({
  selector: 'app-gerenciar-periodos',
  templateUrl: './gerenciar-periodos.component.html',
  styleUrls: ['../../painel-page.css', './gerenciar-periodos.component.css'],
})
export class GerenciarPeriodosComponent implements OnInit {
  periodos: PeriodoResponse[] = [];
  isLoading = true;
  errorMessage = '';

  constructor(
    private readonly periodoService: PeriodoService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.carregarPeriodos();
  }

  get periodoAtivo(): PeriodoResponse | null {
    return this.periodos.find((periodo) => periodo.ativo) ?? null;
  }

  get historicoPeriodos(): PeriodoResponse[] {
    return this.periodos.filter((periodo) => !periodo.ativo);
  }

  abrirCriacao(): void {
    void this.router.navigate(['/painel/criar-periodo']);
  }

  editarPeriodo(periodoId: string): void {
    void this.router.navigate(['/painel/criar-periodo', periodoId]);
  }

  private carregarPeriodos(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.periodoService
      .listarPeriodos()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (periodos) => {
          this.periodos = periodos;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar os períodos letivos.');
        },
      });
  }
}
