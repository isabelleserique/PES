import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { ConsentimentoLgpd, PrivacidadeService } from '../../services/privacidade.service';

@Component({
  selector: 'app-privacidade',
  templateUrl: './privacidade.component.html',
  styleUrls: ['./privacidade.component.css'],
})
export class PrivacidadeComponent implements OnInit {
  isLoading = true;
  isSaving = false;
  errorMessage = '';
  successMessage = '';

  consentimento: ConsentimentoLgpd = {
    publicar_portal_publico: false,
    compartilhar_terceiros: false,
    atualizado_em: null,
  };

  constructor(
    private readonly location: Location,
    private readonly privacidadeService: PrivacidadeService,
  ) {}

  ngOnInit(): void {
    this.carregar();
  }

  salvar(): void {
    if (this.isSaving) return;

    this.isSaving = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.privacidadeService
      .salvarConsentimento(this.consentimento)
      .pipe(finalize(() => (this.isSaving = false)))
      .subscribe({
        next: (consentimento) => {
          this.consentimento = consentimento;
          this.successMessage = 'Suas preferências de privacidade foram atualizadas.';
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível salvar suas preferências de privacidade.');
        },
      });
  }

  voltar(): void {
    this.location.back();
  }

  private carregar(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.privacidadeService
      .getConsentimento()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (consentimento) => {
          this.consentimento = consentimento;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar suas preferências de privacidade.');
        },
      });
  }
}
