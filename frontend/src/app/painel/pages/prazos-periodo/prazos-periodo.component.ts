import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import {
  CronogramaAluno,
  CronogramaOrientando,
  CronogramaPeriodoResponse,
  CronogramaPrazo,
  PainelService,
} from '../../services/painel.service';

export interface PrazoDisplay {
  id: string;
  nomeEtapa: string;
  dataLimite: Date;
  tipoDeTCC: string;
  mensagem: string;
  cor: string;
  status: string;
}

@Component({
  selector: 'app-prazos-periodo',
  templateUrl: './prazos-periodo.component.html',
  styleUrls: ['./prazos-periodo.component.css'],
})
export class PrazosPeriodoComponent implements OnInit {
  readonly filtroTipo = new FormControl<string>('Todos');
  readonly filtroOrientando = new FormControl<string>('');
  readonly tiposDeTCC = ['Todos', 'Monografia', 'Artigo', 'Relatorio de Estagio'];

  nomePeriodo = '';
  statusUsuario = '';
  perfil: 'COORDENADOR' | 'ALUNO' | 'ORIENTADOR' | '' = '';
  nomeContexto = '';
  isLoading = true;
  errorMessage = '';

  private _prazos: PrazoDisplay[] = [];
  private orientandos: CronogramaOrientando[] = [];
  private cronogramaAlunoData: CronogramaAluno | null = null;

  constructor(
    private readonly location: Location,
    private readonly painelService: PainelService,
  ) {}

  ngOnInit(): void {
    this.carregarCronograma();
  }

  get isOrientador(): boolean {
    return this.perfil === 'ORIENTADOR';
  }

  get homeRoute(): string {
    if (this.perfil === 'ALUNO') return '/painel/aluno';
    if (this.perfil === 'ORIENTADOR') return '/painel/orientador';
    if (this.perfil === 'COORDENADOR') return '/painel/coordenador';
    return '/painel';
  }

  get orientandosDisponiveis(): CronogramaOrientando[] {
    return this.orientandos;
  }

  get prazos(): PrazoDisplay[] {
    const filtro = this.filtroTipo.value;
    if (!filtro || filtro === 'Todos') return this._prazos;
    return this._prazos.filter((p) => p.tipoDeTCC === filtro || p.tipoDeTCC === 'Todos');
  }

  get prazosPendentes(): PrazoDisplay[] {
    return this.prazos;
  }

  getDiasRestantes(data: Date): number {
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    const d = new Date(data);
    d.setHours(0, 0, 0, 0);
    return Math.ceil((d.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24));
  }

  getDiasLabel(prazo: PrazoDisplay): string {
    return prazo.mensagem;
  }

  getStatusClass(prazo: PrazoDisplay): string {
    if (prazo.cor === 'vermelho') return 'status-atrasado';
    if (prazo.cor === 'amarelo' || prazo.cor === 'laranja') return 'status-urgente';
    return 'status-ok';
  }

  getTipoEntrega(nomeEtapa: string): string {
    if (nomeEtapa.toLowerCase().includes('defesa')) return 'Defesa';
    return 'Entrega';
  }

  onOrientandoChange(): void {
    this.sincronizarContextoOrientador();
  }

  voltar(): void {
    this.location.back();
  }

  private carregarCronograma(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.painelService.getCronogramaAtivo().subscribe({
      next: (cronograma) => {
        this.aplicarCronograma(cronograma);
        this.isLoading = false;
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar os prazos do período.');
        this.isLoading = false;
      },
    });
  }

  private aplicarCronograma(cronograma: CronogramaPeriodoResponse): void {
    this.nomePeriodo = cronograma.periodo.nome;
    this.perfil = cronograma.perfil;
    this.cronogramaAlunoData = cronograma.aluno;
    this.orientandos = cronograma.orientandos;

    if (cronograma.perfil === 'ALUNO') {
      this.nomeContexto = cronograma.aluno?.titulo_tcc ?? 'Sem TCC registrado';
      this.statusUsuario = cronograma.aluno?.status_tcc ?? 'SEM ENVIO';
      this._prazos = this.mapPrazos(cronograma.aluno?.prazos ?? []);
      return;
    }

    if (cronograma.perfil === 'ORIENTADOR') {
      const selectedId = cronograma.filtro_orientando_id ?? cronograma.orientandos[0]?.aluno_id ?? '';
      this.filtroOrientando.setValue(selectedId, { emitEvent: false });
      this.sincronizarContextoOrientador();
      return;
    }

    this.nomeContexto = 'Cronograma do período ativo';
    this.statusUsuario = cronograma.perfil || 'PERFIL';
    this._prazos = [];
  }

  private sincronizarContextoOrientador(): void {
    const orientandoId = this.filtroOrientando.value;
    const orientando = this.orientandos.find((item) => item.aluno_id === orientandoId) ?? null;

    if (orientando === null) {
      this.nomeContexto = 'Sem orientandos no período ativo';
      this.statusUsuario = 'SEM SOLICITAÇÕES';
      this._prazos = [];
      return;
    }

    this.nomeContexto = orientando.aluno_nome;
    this.statusUsuario = orientando.status_tcc;
    this._prazos = this.mapPrazos(orientando.prazos);
  }

  private mapPrazos(prazos: CronogramaPrazo[]): PrazoDisplay[] {
    return prazos.map((prazo) => ({
      id: prazo.id,
      nomeEtapa: prazo.nome_etapa,
      dataLimite: this.fromISODate(prazo.data_limite),
      tipoDeTCC: prazo.tipo_tcc,
      mensagem: prazo.mensagem,
      cor: prazo.cor,
      status: prazo.status,
    }));
  }

  private fromISODate(value: string): Date {
    const [year, month, day] = value.split('-').map(Number);
    return new Date(year, month - 1, day);
  }
}
