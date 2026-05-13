import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import {
  CreatePeriodoPayload,
  PeriodoResponse,
  PeriodoService,
  TipoDeTCC,
} from '../../services/periodo.service';

interface LocalPrazo {
  localId: string;
  nomeEtapa: string;
  dataLimite: Date;
  tipoDeTCC: TipoDeTCC;
}

@Component({
  selector: 'app-criar-periodo',
  templateUrl: './criar-periodo.component.html',
  styleUrls: ['../../painel-page.css', './criar-periodo.component.css'],
})
export class CriarPeriodoComponent implements OnInit {
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
  isLoadingPeriodo = false;
  errorMessage = '';
  successMessage = '';
  periodoId: string | null = null;

  readonly etapas = ['Definição de Tema/Orientador', 'Aceite do Orientador', 'Entregáveis'];
  readonly tiposDeTCC: TipoDeTCC[] = ['Todos', 'Monografia', 'Artigo', 'Relatorio de Estagio'];

  constructor(
    private readonly fb: FormBuilder,
    private readonly periodoService: PeriodoService,
    private readonly router: Router,
    private readonly route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const periodoId = this.route.snapshot.paramMap.get('periodoId');
    if (!periodoId) {
      return;
    }

    this.periodoId = periodoId;
    this.carregarPeriodo(periodoId);
  }

  get isEditMode(): boolean {
    return this.periodoId !== null;
  }

  get pageTitle(): string {
    return this.isEditMode
      ? 'Edição do Período Letivo Ativo'
      : 'Criação e Configuração do Período Letivo';
  }

  get submitLabel(): string {
    if (this.isSubmitting) {
      return this.isEditMode ? 'Salvando alterações...' : 'Salvando...';
    }

    return this.isEditMode ? 'Salvar Alterações' : 'Salvar Período';
  }

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
    void this.router.navigate(['/painel/gerenciar-periodos']);
  }

  salvarPeriodo(): void {
    this.periodoForm.markAllAsTouched();
    if (this.periodoForm.invalid || this.isSubmitting || this.isLoadingPeriodo) return;

    this.isSubmitting = true;
    this.errorMessage = '';
    this.successMessage = '';

    const payload = this.buildPayload();
    const request$ = this.periodoId
      ? this.periodoService.atualizarPeriodo(this.periodoId, payload)
      : this.periodoService.criarPeriodo(payload);

    const wasEditMode = this.isEditMode;

    request$
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: (periodo) => {
          this.syncFormWithPeriodo(periodo);
          this.periodoId = periodo.id;
          this.successMessage = wasEditMode
            ? 'Período letivo atualizado com sucesso!'
            : 'Período letivo criado com sucesso!';
          setTimeout(() => void this.router.navigate(['/painel/gerenciar-periodos']), 1200);
        },
        error: (err: unknown) => {
          this.errorMessage = getApiErrorMessage(err, 'Não foi possível salvar o período letivo.');
        },
      });
  }

  private carregarPeriodo(periodoId: string): void {
    this.isLoadingPeriodo = true;
    this.errorMessage = '';

    this.periodoService
      .getPeriodoById(periodoId)
      .pipe(finalize(() => (this.isLoadingPeriodo = false)))
      .subscribe({
        next: (periodo) => {
          this.syncFormWithPeriodo(periodo);
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar o período letivo.');
        },
      });
  }

  private syncFormWithPeriodo(periodo: PeriodoResponse): void {
    this.periodoForm.reset({
      nome: periodo.nome,
      dataInicio: this.fromISODate(periodo.data_inicio),
      dataFim: this.fromISODate(periodo.data_fim),
      ativo: periodo.ativo,
    });
    this.prazos = periodo.prazos.map((prazo) => ({
      localId: prazo.id,
      nomeEtapa: prazo.nome_etapa,
      dataLimite: this.fromISODate(prazo.data_limite),
      tipoDeTCC: prazo.tipo_tcc,
    }));
    this.showPrazoForm = false;
    this.editingId = null;
  }

  private buildPayload(): CreatePeriodoPayload {
    const { nome, dataInicio, dataFim, ativo } = this.periodoForm.getRawValue();

    return {
      nome: nome!,
      data_inicio: this.toISODate(dataInicio!),
      data_fim: this.toISODate(dataFim!),
      ativo: ativo!,
      prazos: this.prazos.map((p) => ({
        nome_etapa: p.nomeEtapa,
        data_limite: this.toISODate(p.dataLimite),
        tipo_tcc: p.tipoDeTCC,
      })),
    };
  }

  private toISODate(date: Date): string {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  private fromISODate(value: string): Date {
    const [year, month, day] = value.split('-').map(Number);
    return new Date(year, month - 1, day);
  }
}
