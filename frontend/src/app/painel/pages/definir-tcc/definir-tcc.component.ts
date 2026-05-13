import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin, of, throwError } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import {
  CronogramaAluno,
  CronogramaPeriodoResponse,
  PainelService,
  TccPayload,
  TccResponse,
  TipoTccAluno,
} from '../../services/painel.service';

export interface Professor {
  id: string;
  nome: string;
  area: string;
}

const TIPO_TCC_BY_LABEL: Record<string, TipoTccAluno> = {
  Monografia: 'Monografia',
  'Relatório de Estágio': 'Relatorio de Estagio',
  'Artigo Científico': 'Artigo',
};

const TIPO_TCC_LABEL_BY_VALUE: Record<TipoTccAluno, string> = {
  Monografia: 'Monografia',
  'Relatorio de Estagio': 'Relatório de Estágio',
  Artigo: 'Artigo Científico',
};

@Component({
  selector: 'app-definir-tcc',
  templateUrl: './definir-tcc.component.html',
  styleUrls: ['./definir-tcc.component.css'],
})
export class DefinirTccComponent implements OnInit {
  readonly step1Form = this.fb.nonNullable.group({
    titulo: ['', [Validators.required, Validators.minLength(3)]],
    tipoDeTCC: ['Artigo Científico', Validators.required],
    resumo: ['', Validators.required],
  });

  readonly step2Form = this.fb.nonNullable.group({
    orientadorId: ['', Validators.required],
  });

  readonly step3Form = this.fb.nonNullable.group({
    coorientadorId: [''],
  });

  readonly tiposDeTCC = ['Monografia', 'Relatório de Estágio', 'Artigo Científico'];

  professores: Professor[] = [];
  cronograma: CronogramaPeriodoResponse | null = null;
  meuTcc: TccResponse | null = null;
  isLoading = true;
  isSubmitting = false;
  isSubmitted = false;
  submittedAction: 'create' | 'update' = 'create';
  errorMessage = '';
  searchOrientador = '';
  searchCoorientador = '';
  orientadorSelecionado: Professor | null = null;
  coorientadorSelecionado: Professor | null = null;
  prazoDefinicao: Date | null = null;

  constructor(
    private readonly fb: FormBuilder,
    private readonly location: Location,
    private readonly painelService: PainelService,
    private readonly router: Router,
  ) {
    this.step2Form.controls.orientadorId.valueChanges.subscribe((orientadorId) => {
      this.orientadorSelecionado = this.professores.find((prof) => prof.id === orientadorId) ?? null;

      if (this.step3Form.controls.coorientadorId.getRawValue() === orientadorId) {
        this.limparCoorientador();
      }
    });

    this.step3Form.controls.coorientadorId.valueChanges.subscribe((coorientadorId) => {
      this.coorientadorSelecionado = this.professores.find((prof) => prof.id === coorientadorId) ?? null;
    });
  }

  ngOnInit(): void {
    this.loadPageData();
  }

  get cronogramaAluno(): CronogramaAluno | null {
    return this.cronograma?.aluno ?? null;
  }

  get statusAtual(): string {
    return this.meuTcc?.status ?? 'SEM ENVIO';
  }

  get resumoPrazo(): string | null {
    return this.meuTcc?.alerta_prazo ?? this.cronogramaAluno?.alerta_prazo ?? null;
  }

  get tipoSelecionadoLabel(): string {
    return this.step1Form.controls.tipoDeTCC.getRawValue();
  }

  get successTitle(): string {
    return this.submittedAction === 'update'
      ? 'Dados do TCC atualizados com sucesso!'
      : 'Solicitação enviada com sucesso!';
  }

  get successDescription(): string {
    if (this.submittedAction === 'update') {
      return 'As alterações foram registradas e o orientador foi notificado sobre a atualização.';
    }

    return `O orientador ${this.orientadorSelecionado?.nome ?? ''} foi notificado e irá analisar sua solicitação.`;
  }

  get successStatusLabel(): string {
    if (this.submittedAction === 'update') {
      return this.meuTcc?.status ?? 'Atualizado';
    }

    return 'Aguardando Aceite do Orientador';
  }

  get submitButtonLabel(): string {
    if (this.isSubmitting) {
      return this.meuTcc ? 'Atualizando...' : 'Enviando...';
    }

    return this.meuTcc ? 'Atualizar TCC' : 'Submeter para Aceite';
  }

  get foraDoPrazo(): boolean {
    if (!this.prazoDefinicao) {
      return false;
    }

    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    return hoje > this.prazoDefinicao;
  }

  get diasAtraso(): number {
    if (!this.prazoDefinicao) {
      return 0;
    }

    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    return Math.ceil((hoje.getTime() - this.prazoDefinicao.getTime()) / (1000 * 60 * 60 * 24));
  }

  get professoresFiltrados(): Professor[] {
    const q = this.searchOrientador.trim().toLowerCase();
    if (!q) {
      return this.professores;
    }

    return this.professores.filter(
      (prof) => prof.nome.toLowerCase().includes(q) || prof.area.toLowerCase().includes(q),
    );
  }

  get coorientadoresFiltrados(): Professor[] {
    const base = this.orientadorSelecionado
      ? this.professores.filter((prof) => prof.id !== this.orientadorSelecionado?.id)
      : this.professores;
    const q = this.searchCoorientador.trim().toLowerCase();

    if (!q) {
      return base;
    }

    return base.filter(
      (prof) => prof.nome.toLowerCase().includes(q) || prof.area.toLowerCase().includes(q),
    );
  }

  selecionarOrientador(prof: Professor): void {
    this.step2Form.patchValue({ orientadorId: prof.id });
  }

  selecionarCoorientador(prof: Professor): void {
    this.step3Form.patchValue({ coorientadorId: prof.id });
  }

  limparCoorientador(): void {
    this.step3Form.patchValue({ coorientadorId: '' });
  }

  onSearchOrientador(event: Event): void {
    this.searchOrientador = (event.target as HTMLInputElement).value;
  }

  onSearchCoorientador(event: Event): void {
    this.searchCoorientador = (event.target as HTMLInputElement).value;
  }

  submeter(): void {
    this.step1Form.markAllAsTouched();
    this.step2Form.markAllAsTouched();

    if (this.step1Form.invalid || this.step2Form.invalid || this.isSubmitting) {
      return;
    }

    const payload = this.buildPayload();
    const alreadyHadTcc = this.meuTcc !== null;

    this.isSubmitting = true;
    this.errorMessage = '';

    const request$ = alreadyHadTcc
      ? this.painelService.atualizarMeuTcc(payload)
      : this.painelService.criarMeuTcc(payload);

    request$
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: (response) => {
          this.submittedAction = alreadyHadTcc ? 'update' : 'create';
          this.meuTcc = response;
          this.syncFormWithTcc(response);
          this.reloadCronograma();
          this.isSubmitted = true;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível salvar a definição do TCC.');
        },
      });
  }

  cancelar(): void {
    void this.router.navigate(['/painel/aluno']);
  }

  voltar(): void {
    this.location.back();
  }

  private loadPageData(): void {
    this.isLoading = true;
    this.errorMessage = '';

    forkJoin({
      cronograma: this.painelService.getCronogramaAtivo(),
      orientadores: this.painelService.listarOrientadoresDisponiveis(),
      tcc: this.painelService.getMeuTcc().pipe(
        catchError((error: unknown) => (this.isNotFound(error) ? of(null) : throwError(() => error))),
      ),
    })
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: ({ cronograma, orientadores, tcc }) => {
          this.cronograma = cronograma;
          this.professores = orientadores.map((orientador) => ({
            id: orientador.id,
            nome: orientador.nome_completo,
            area: orientador.email,
          }));
          this.meuTcc = tcc;
          this.prazoDefinicao = this.resolvePrazoDefinicao(cronograma);
          this.syncFormWithTcc(tcc);
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar a tela de definição de TCC.');
        },
      });
  }

  private reloadCronograma(): void {
    this.painelService.getCronogramaAtivo().subscribe({
      next: (cronograma) => {
        this.cronograma = cronograma;
        this.prazoDefinicao = this.resolvePrazoDefinicao(cronograma);
      },
      error: () => {
        this.prazoDefinicao = this.resolvePrazoDefinicao(this.cronograma);
      },
    });
  }

  private syncFormWithTcc(tcc: TccResponse | null): void {
    if (tcc === null) {
      this.step1Form.reset({
        titulo: '',
        tipoDeTCC: 'Artigo Científico',
        resumo: '',
      });
      this.step2Form.reset({ orientadorId: '' });
      this.step3Form.reset({ coorientadorId: '' });
      this.orientadorSelecionado = null;
      this.coorientadorSelecionado = null;
      return;
    }

    this.step1Form.reset({
      titulo: tcc.titulo,
      tipoDeTCC: TIPO_TCC_LABEL_BY_VALUE[tcc.tipo_tcc],
      resumo: '',
    });
    this.step2Form.reset({ orientadorId: tcc.orientador_id });
    this.step3Form.reset({ coorientadorId: tcc.coorientador_id ?? '' });
    this.orientadorSelecionado = this.professores.find((prof) => prof.id === tcc.orientador_id) ?? null;
    this.coorientadorSelecionado = this.professores.find((prof) => prof.id === tcc.coorientador_id) ?? null;
  }

  private buildPayload(): TccPayload {
    const step1 = this.step1Form.getRawValue();
    const step2 = this.step2Form.getRawValue();
    const step3 = this.step3Form.getRawValue();

    return {
      titulo: step1.titulo.trim(),
      tipo_tcc: TIPO_TCC_BY_LABEL[step1.tipoDeTCC],
      orientador_id: step2.orientadorId,
      ...(step3.coorientadorId ? { coorientador_id: step3.coorientadorId } : {}),
    };
  }

  private resolvePrazoDefinicao(cronograma: CronogramaPeriodoResponse | null): Date | null {
    const prazoDefinicao = cronograma?.aluno?.prazos?.find((prazo) => {
      const nomeEtapa = prazo.nome_etapa.toLowerCase();
      return nomeEtapa.includes('defin') || nomeEtapa.includes('tema');
    });

    if (!prazoDefinicao) {
      return null;
    }

    return this.fromISODate(prazoDefinicao.data_limite);
  }

  private fromISODate(value: string): Date {
    const [year, month, day] = value.split('-').map(Number);
    return new Date(year, month - 1, day);
  }

  private isNotFound(error: unknown): boolean {
    return (
      typeof error === 'object'
      && error !== null
      && 'status' in error
      && (error as { status?: unknown }).status === 404
    );
  }
}
