import { Component } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { BuscarTccParams, PublicoService, TccPublico } from '../../services/publico.service';

@Component({
  selector: 'app-buscar-tcc',
  templateUrl: './buscar-tcc.component.html',
  styleUrls: ['./buscar-tcc.component.css'],
})
export class BuscarTccComponent {
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

  constructor(
    private readonly fb: FormBuilder,
    private readonly publicoService: PublicoService,
    private readonly router: Router,
  ) {}

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
