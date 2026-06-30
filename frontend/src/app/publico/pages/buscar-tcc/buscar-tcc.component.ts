import { Component } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { AuthService } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { BuscarTccParams, PublicoService, TccPublico } from '../../services/publico.service';

interface ProfessorPublico {
  nome: string;
  titulo: string;
  objetosEstudo: string[];
  descricao: string;
  foto: string;
}

@Component({
  selector: 'app-buscar-tcc',
  templateUrl: './buscar-tcc.component.html',
  styleUrls: ['./buscar-tcc.component.css'],
})
export class BuscarTccComponent {
  readonly professores: ProfessorPublico[] = [
    {
      nome: 'Prof. Ana Ribeiro',
      titulo: 'Engenharia de Software e Sistemas Web',
      objetosEstudo: ['Qualidade de software', 'UX aplicada', 'Arquitetura web'],
      descricao: 'Pesquisa processos, ferramentas e práticas para desenvolvimento de sistemas confiáveis e sustentáveis.',
      foto: 'AR',
    },
    {
      nome: 'Prof. Bruno Almeida',
      titulo: 'Inteligência Artificial e Ciência de Dados',
      objetosEstudo: ['Aprendizado de máquina', 'Mineração de dados', 'Modelos preditivos'],
      descricao: 'Orienta trabalhos com foco em análise de dados, automação inteligente e apoio à decisão.',
      foto: 'BA',
    },
    {
      nome: 'Prof. Camila Torres',
      titulo: 'Redes, Segurança e Sistemas Distribuídos',
      objetosEstudo: ['Segurança da informação', 'Computação em nuvem', 'Internet das Coisas'],
      descricao: 'Atua em temas ligados à infraestrutura, proteção de dados e sistemas conectados.',
      foto: 'CT',
    },
  ];

  readonly form = this.fb.nonNullable.group({
    titulo: [''],
    aluno: [''],
    area_tematica: [''],
    curso: [''],
  });

  isLoading = false;
  errorMessage = '';
  resultados: TccPublico[] = [];
  buscaRealizada = false;
  readonly isAuthenticated: boolean;
  readonly painelRoute: string[];

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly publicoService: PublicoService,
    private readonly router: Router,
  ) {
    this.isAuthenticated = this.authService.isAuthenticated();
    this.painelRoute = this.authService.getPostLoginRoute();
  }

  buscar(): void {
    if (this.isLoading) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.buscaRealizada = false;

    this.publicoService.buscarTcc(this.buildParams())
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (resultados) => {
          this.resultados = resultados;
          this.buscaRealizada = true;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível realizar a busca.');
        },
      });
  }

  verDetalhe(id: string): void {
    void this.router.navigate(['/consultor-externo', id]);
  }

  private buildParams(): BuscarTccParams {
    const values = this.form.getRawValue();
    return {
      ...(values.titulo.trim() ? { titulo: values.titulo.trim() } : {}),
      ...(values.aluno.trim() ? { aluno: values.aluno.trim() } : {}),
      ...(values.area_tematica.trim() ? { area_tematica: values.area_tematica.trim() } : {}),
      ...(values.curso.trim() ? { curso: values.curso.trim() } : {}),
    };
  }
}
