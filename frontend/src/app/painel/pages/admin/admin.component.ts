import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { AuthService } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { AuthenticatedUserProfile, PainelService } from '../../services/painel.service';

@Component({
  selector: 'app-painel-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css'],
})
export class PainelAdminComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  currentUser: AuthenticatedUserProfile | null = null;

  constructor(
    private readonly authService: AuthService,
    private readonly painelService: PainelService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.painelService
      .getMeuPerfil()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (user) => {
          this.currentUser = user;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar o painel administrativo.');
        },
      });
  }

  logout(): void {
    this.authService.clearSession();
    void this.router.navigate(['/auth/login']);
  }
}
