import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { ProfessorPublicoDetalhe, PublicoService } from '../../services/publico.service';

@Component({
  selector: 'app-detalhe-professor',
  templateUrl: './detalhe-professor.component.html',
  styleUrls: ['./detalhe-professor.component.css'],
})
export class DetalheProfessorComponent implements OnInit {
  isLoading = true;
  errorMessage = '';
  professor: ProfessorPublicoDetalhe | null = null;

  constructor(
    private readonly location: Location,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly publicoService: PublicoService,
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.carregar(id);
    }
  }

  verTcc(id: string): void {
    void this.router.navigate(['/tcc', id]);
  }

  voltar(): void {
    this.location.back();
  }

  private carregar(id: string): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.publicoService.getDetalheProfessor(id).subscribe({
      next: (professor) => {
        this.professor = professor;
        this.isLoading = false;
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar o perfil do professor.');
        this.isLoading = false;
      },
    });
  }
}
