import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { PeriodoService, TipoDeTCC } from '../../services/periodo.service';

interface LocalPrazo {
  localId: string;
  nomeEtapa: string;
  dataLimite: Date;
  tipoDeTCC: TipoDeTCC;
}

@Component({
  selector: 'app-criar-periodo',
  templateUrl: './criar-periodo.component.html',
  styleUrls: ['./criar-periodo.component.css'],
})
export class CriarPeriodoComponent {
  readonly periodoForm = this.fb.group({
    nome: ['', Validators.required],
    dataInicio: [null as Date | null, Validators.required],
    dataFim: [null as Date | null, Validators.required],
    ativo: [false],
  });

  readonly prazoForm = this.fb.group({
    nomeEtapa: ['', Validators.required],
    dataLimite: [null as Date | null, Validators.required],
    tipoDeTCC: ['Todos' as TipoDeTCC, Validators.required],
  });

  prazos: LocalPrazo[] = [];
  showPrazoForm = false;
  editingId: string | null = null;
  isSubmitting = false;
  errorMessage = '';
  successMessage = '';

  readonly etapas = ['Definição de Tema/Orientador', 'Aceite do Orientador', 'Entregáveis'];
  readonly tiposDeTCC: TipoDeTCC[] = ['Todos', 'Monografia', 'Artigo'];

  constructor(
    private readonly fb: FormBuilder,
    private readonly periodoService: PeriodoService,
    private readonly router: Router,
  ) {}

  abrirFormPrazo(): void {
    this.editingId = null;
    this.prazoForm.reset({ tipoDeTCC: 'Todos' });
    this.showPrazoForm = true;
  }

  editarPrazo(prazo: LocalPrazo): void {
    this.editingId = prazo.localId;
    this.prazoForm.setValue({
      nomeEtapa: prazo.nomeEtapa,
      dataLimite: prazo.dataLimite,
      tipoDeTCC: prazo.tipoDeTCC,
    });
    this.showPrazoForm = true;
  }

  confirmarPrazo(): void {
    this.prazoForm.markAllAsTouched();
    if (this.prazoForm.invalid) return;

    const { nomeEtapa, dataLimite, tipoDeTCC } = this.prazoForm.getRawValue();

    if (this.editingId) {
      this.prazos = this.prazos.map((p) =>
        p.localId === this.editingId
          ? { ...p, nomeEtapa: nomeEtapa!, dataLimite: dataLimite!, tipoDeTCC: tipoDeTCC! }
          : p,
      );
    } else {
      this.prazos = [
        ...this.prazos,
        {
          localId: Math.random().toString(36).slice(2),
          nomeEtapa: nomeEtapa!,
          dataLimite: dataLimite!,
          tipoDeTCC: tipoDeTCC!,
        },
      ];
    }

    this.showPrazoForm = false;
    this.editingId = null;
  }

  cancelarFormPrazo(): void {
    this.showPrazoForm = false;
    this.editingId = null;
  }

  removerPrazo(localId: string): void {
    this.prazos = this.prazos.filter((p) => p.localId !== localId);
  }

  cancelar(): void {
    void this.router.navigate(['/painel/coordenador']);
  }

  salvarPeriodo(): void {
    this.periodoForm.markAllAsTouched();
    if (this.periodoForm.invalid || this.isSubmitting) return;

    this.isSubmitting = true;
    this.errorMessage = '';
    this.successMessage = '';

    const { nome, dataInicio, dataFim, ativo } = this.periodoForm.getRawValue();

    this.periodoService
      .criarPeriodo({
        nome: nome!,
        data_inicio: this.toISODate(dataInicio!),
        data_fim: this.toISODate(dataFim!),
        ativo: ativo!,
        prazos: this.prazos.map((p) => ({
          nome_etapa: p.nomeEtapa,
          data_limite: this.toISODate(p.dataLimite),
          tipo_tcc: p.tipoDeTCC,
        })),
      })
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: () => {
          this.successMessage = 'Período letivo criado com sucesso!';
          setTimeout(() => void this.router.navigate(['/painel/coordenador']), 1500);
        },
        error: (err: unknown) => {
          this.errorMessage = getApiErrorMessage(err, 'Não foi possível salvar o período letivo.');
        },
      });
  }

  private toISODate(date: Date): string {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }
}
