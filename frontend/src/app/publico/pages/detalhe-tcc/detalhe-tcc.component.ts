import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ActivatedRoute } from '@angular/router';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { PublicoService, TccPublicoDetalhe } from '../../services/publico.service';

@Component({
  selector: 'app-detalhe-tcc',
  templateUrl: './detalhe-tcc.component.html',
  styleUrls: ['./detalhe-tcc.component.css'],
})
export class DetalheTccComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  tcc: TccPublicoDetalhe | null = null;
  safePreviewUrl: SafeResourceUrl | null = null;

  constructor(
    private readonly location: Location,
    private readonly route: ActivatedRoute,
    private readonly publicoService: PublicoService,
    private readonly sanitizer: DomSanitizer,
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.errorMessage = 'Trabalho não informado.';
      this.isLoading = false;
      return;
    }
    this.carregar(id);
  }

  voltar(): void {
    this.location.back();
  }

  abrirPreview(url: string): void {
    this.safePreviewUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  fecharPreview(): void {
    this.safePreviewUrl = null;
  }

  private carregar(id: string): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.publicoService.getDetalheTcc(id).subscribe({
      next: (tcc) => {
        this.tcc = tcc;
        this.isLoading = false;
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar os detalhes do trabalho.');
        this.isLoading = false;
      },
    });
  }
}
