import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { finalize } from 'rxjs/operators';

import { AuthService, UserPerfil } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { NotificacaoService, PreferenciasNotificacao } from '../../services/notificacao.service';

@Component({
  selector: 'app-notificacoes',
  templateUrl: './notificacoes.component.html',
  styleUrls: ['./notificacoes.component.css'],
})
export class NotificacoesComponent implements OnInit {
  isLoading = true;
  isSaving = false;
  errorMessage = '';
  successMessage = '';

  readonly perfil: UserPerfil | null = this.authService.getStoredPerfil();
  readonly antecedenciaOpcoes = [3, 5, 7, 15];

  prefs: PreferenciasNotificacao = {
    email_prazos_orientandos: true,
    antecedencia_dias: 3,
    email_notas_parciais: true,
    email_notas_finais: true,
  };

  constructor(
    private readonly location: Location,
    private readonly authService: AuthService,
    private readonly notificacaoService: NotificacaoService,
  ) {}

  get isOrientador(): boolean {
    return this.perfil === 'ORIENTADOR';
  }

  get isAluno(): boolean {
    return this.perfil === 'ALUNO';
  }

  get homePath(): string {
    switch (this.perfil) {
      case 'ADMIN':
        return '/painel/admin';
      case 'ORIENTADOR':
        return '/painel/orientador';
      case 'COORDENADOR':
        return '/painel/coordenador';
      default:
        return '/painel/aluno';
    }
  }

  ngOnInit(): void {
    this.carregar();
  }

  salvar(): void {
    if (this.isSaving) return;

    this.isSaving = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.notificacaoService
      .salvarPreferencias(this.prefs)
      .pipe(finalize(() => (this.isSaving = false)))
      .subscribe({
        next: (prefs) => {
          this.prefs = prefs;
          this.successMessage = 'Preferências de notificação salvas com sucesso.';
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível salvar as preferências.');
        },
      });
  }

  voltar(): void {
    this.location.back();
  }

  private carregar(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.notificacaoService
      .getPreferencias()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (prefs) => {
          this.prefs = prefs;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar as preferências.');
        },
      });
  }
}
