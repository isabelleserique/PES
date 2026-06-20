import { Component } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { BuscarProfessoresParams, ProfessorPublico, PublicoService } from '../../services/publico.service';

@Component({
  selector: 'app-listar-professores',
  templateUrl: './listar-professores.component.html',
  styleUrls: ['./listar-professores.component.css'],
})
export class ListarProfessoresComponent {
  readonly form: FormGroup;
  isLoading = false;
  errorMessage = '';
  resultados: ProfessorPublico[] = [];
  buscaRealizada = false;

  constructor(
    private readonly fb: FormBuilder,
    private readonly publicoService: PublicoService,
    private readonly router: Router,
  ) {
    this.form = this.fb.nonNullable.group({
      nome: [''],
      area: [''],
    });
  }

  buscar(): void {
    if (this.isLoading) return;

    this.isLoading = true;
    this.errorMessage = '';
    this.buscaRealizada = false;

    const params: BuscarProfessoresParams = {};
    const v = this.form.getRawValue() as Record<string, string>;
    if (v['nome']?.trim()) params.nome = v['nome'].trim();
    if (v['area']?.trim()) params.area = v['area'].trim();

    this.publicoService.buscarProfessores(params)
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

  verPerfil(id: string): void {
    void this.router.navigate(['/tcc/professores', id]);
  }
}
