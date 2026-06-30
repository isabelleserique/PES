import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { PainelService, VisaoGeralAlunoDetalhe, VisaoGeralPeriodo } from '../../services/painel.service';

@Component({
  selector: 'app-visao-geral',
  templateUrl: './visao-geral.component.html',
  styleUrls: ['./visao-geral.component.css'],
})
export class VisaoGeralComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  dados: VisaoGeralPeriodo | null = null;

  constructor(
    private readonly location: Location,
    private readonly painelService: PainelService,
  ) {}

  ngOnInit(): void {
    this.carregar();
  }

  get alunosComRisco(): VisaoGeralAlunoDetalhe[] {
    return (this.dados?.alunos_detalhados ?? []).filter(
      (aluno) => aluno.sem_orientador_aceito || aluno.prazos_vencidos_sem_entrega > 0,
    );
  }

  voltar(): void {
    this.location.back();
  }

  private carregar(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.painelService.getVisaoGeralPeriodo().subscribe({
      next: (dados) => {
        this.dados = dados;
        this.isLoading = false;
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar a visão geral do período.');
        this.isLoading = false;
      },
    });
  }
}
