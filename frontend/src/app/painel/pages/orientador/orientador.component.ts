import { Component, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { AuthService } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import {
  AuthenticatedUserProfile,
  CronogramaOrientando,
  CronogramaPeriodoResponse,
  PainelService,
} from '../../services/painel.service';

@Component({
  selector: 'app-painel-orientador',
  templateUrl: './orientador.component.html',
  styleUrls: ['../../painel-page.css'],
})
export class PainelOrientadorComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  currentUser: AuthenticatedUserProfile | null = null;
  cronograma: CronogramaPeriodoResponse | null = null;
  readonly filtroForm = this.fb.nonNullable.group({
    orientando_id: [''],
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly painelService: PainelService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadPainel();
  }

  get orientandosVisiveis(): CronogramaOrientando[] {
    const orientandoId = this.filtroForm.controls.orientando_id.getRawValue();
    const orientandos = this.cronograma?.orientandos ?? [];
    return orientandoId ? orientandos.filter((orientando) => orientando.aluno_id === orientandoId) : orientandos;
  }

  logout(): void {
    this.authService.clearSession();
    void this.router.navigate(['/auth/login']);
  }

  private loadPainel(): void {
    this.isLoading = true;
    this.errorMessage = '';

    forkJoin({
      user: this.painelService.getMeuPerfil(),
      cronograma: this.painelService.getCronogramaAtivo(),
    })
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: ({ user, cronograma }) => {
          this.currentUser = user;
          this.cronograma = cronograma;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel carregar o painel do orientador.');
        },
      });
  }
}
