import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, of } from 'rxjs';
import { finalize, switchMap } from 'rxjs/operators';

import { AuthService } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import {
  AuthenticatedUserProfile,
  PainelService,
  PendingRegistration,
  ReviewRegistrationPayload,
} from '../../services/painel.service';

@Component({
  selector: 'app-painel-coordenador',
  templateUrl: './painel.component.html',
  styleUrls: ['../../painel-page.css'],
})
export class PainelCoordenadorComponent implements OnInit {
  isLoading = true;
  isReviewing = false;
  feedbackMessage = '';
  errorMessage = '';
  currentUser: AuthenticatedUserProfile | null = null;
  pendingRegistrations: PendingRegistration[] = [];

  constructor(
    private readonly authService: AuthService,
    private readonly painelService: PainelService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadPainelData();
  }

  get isCoordenador(): boolean {
    return this.currentUser?.perfil === 'COORDENADOR';
  }

  logout(): void {
    this.authService.clearSession();
    void this.router.navigate(['/auth/login']);
  }

  revisarCadastro(userId: string, acao: ReviewRegistrationPayload['acao']): void {
    if (this.isReviewing) {
      return;
    }

    this.isReviewing = true;
    this.feedbackMessage = '';
    this.errorMessage = '';

    this.painelService
      .revisarCadastro(userId, { acao })
      .pipe(finalize(() => (this.isReviewing = false)))
      .subscribe({
        next: () => {
          this.pendingRegistrations = this.pendingRegistrations.filter((item) => item.id !== userId);
          this.feedbackMessage =
            acao === 'APROVAR'
              ? 'Cadastro aprovado com sucesso.'
              : 'Cadastro rejeitado com sucesso.';
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel concluir a revisao do cadastro.');
        },
      });
  }

  private loadPainelData(): void {
    this.isLoading = true;
    this.feedbackMessage = '';
    this.errorMessage = '';

    this.painelService
      .getMeuPerfil()
      .pipe(
        switchMap((user) => {
          this.currentUser = user;
          return this.getPendingRegistrationsIfNeeded(user);
        }),
        finalize(() => (this.isLoading = false)),
      )
      .subscribe({
        next: (pendingRegistrations) => {
          this.pendingRegistrations = pendingRegistrations;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Nao foi possivel carregar o painel.');
        },
      });
  }

  private getPendingRegistrationsIfNeeded(
    user: AuthenticatedUserProfile,
  ): Observable<PendingRegistration[]> {
    if (user.perfil !== 'COORDENADOR') {
      return of([]);
    }

    return this.painelService.listarPendentes();
  }
}
