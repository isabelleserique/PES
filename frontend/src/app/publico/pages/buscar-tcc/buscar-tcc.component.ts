import { Component } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
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
  readonly form: FormGroup;
  isLoading = false;
  errorMessage = '';
  resultados: TccPublico[] = [];
  buscaRealizada = false;

  constructor(
    private readonly fb: FormBuilder,
    private readonly publicoService: PublicoService,
    private readonly router: Router,
  ) {
    this.form = this.fb.nonNullable.group({
      titulo: [''],
      aluno: [''],
      area_tematica: [''],
      curso: [''],
    });
  }

  buscar(): void {
    if (this.isLoading) return;

    this.isLoading = true;
    this.errorMessage = '';
    this.buscaRealizada = false;

    const params: BuscarTccParams = {};
    const v = this.form.getRawValue() as Record<string, string>;
    if (v['titulo']?.trim()) params.titulo = v['titulo'].trim();
    if (v['aluno']?.trim()) params.aluno = v['aluno'].trim();
    if (v['area_tematica']?.trim()) params.area_tematica = v['area_tematica'].trim();
    if (v['curso']?.trim()) params.curso = v['curso'].trim();

    this.publicoService.buscarTcc(params)
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
    void this.router.navigate(['/tcc', id]);
  }
}
