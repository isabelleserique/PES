import { Location } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin, Observable } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { CronogramaPrazo, PainelService, TccResponse, TipoTccAluno } from '../../services/painel.service';
import { EtapaEntregavel, SubmissaoEntregavel, SubmissaoService } from '../../services/submissao.service';

const ETAPAS_BY_TIPO: Record<TipoTccAluno, EtapaEntregavel[]> = {
  Monografia: ['Revisão Bibliográfica', '1ª Entrega', '2ª Entrega', 'Monografia Final'],
  'Relatorio de Estagio': ['1º Entregável intermediário', '2º Entregável intermediário', 'Relatório Final'],
  Artigo: ['Artigo Científico'],
};

@Component({
  selector: 'app-submeter-artigo',
  templateUrl: './submeter-artigo.component.html',
  styleUrls: ['./submeter-artigo.component.css'],
})
export class SubmeterArtigoComponent implements OnInit {
  @ViewChild('artigoInput') artigoInput!: ElementRef<HTMLInputElement>;
  @ViewChild('comprovanteInput') comprovanteInput!: ElementRef<HTMLInputElement>;

  arquivoFile: File | null = null;
  comprovanteFile: File | null = null;
  readonly foiAceitoCtrl = new FormControl(false);
  readonly etapaCtrl = new FormControl<EtapaEntregavel | null>(null);

  isSubmitting = false;
  isSubmitted = false;
  isLoading = true;
  errorMessage = '';
  notaAtribuida: number | null = null;
  meuTcc: TccResponse | null = null;
  prazos: CronogramaPrazo[] = [];

  prazoSubmissao: Date | null = null;
  historico: SubmissaoEntregavel[] = [];

  get foiAceito(): boolean {
    return this.isArtigo && !!this.foiAceitoCtrl.value;
  }

  get foraDoPrazo(): boolean {
    if (!this.prazoSubmissao) return false;
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    return hoje > this.prazoSubmissao;
  }

  get diasAtraso(): number {
    if (!this.prazoSubmissao) return 0;
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    return Math.ceil((hoje.getTime() - this.prazoSubmissao.getTime()) / (1000 * 60 * 60 * 24));
  }

  get podeSubmeter(): boolean {
    if (!this.arquivoFile) return false;
    if (!this.isArtigo && !this.etapaCtrl.value) return false;
    if (this.foiAceito && !this.comprovanteFile) return false;
    return true;
  }

  get isArtigo(): boolean {
    return this.meuTcc?.tipo_tcc === 'Artigo';
  }

  get tipoTccLabel(): string {
    if (this.meuTcc?.tipo_tcc === 'Relatorio de Estagio') return 'Relatório de Estágio';
    return this.meuTcc?.tipo_tcc ?? 'TCC';
  }

  get pageTitle(): string {
    return this.isArtigo ? 'Submissão de Artigo Científico' : `Submissão de Entregáveis - ${this.tipoTccLabel}`;
  }

  get arquivoLabel(): string {
    return this.isArtigo ? 'Arquivo do Artigo' : 'Arquivo do Entregável';
  }

  get submitLabel(): string {
    return this.isSubmitting ? 'Enviando...' : (this.isArtigo ? 'Submeter Artigo' : 'Submeter Entregável');
  }

  get etapasDisponiveis(): EtapaEntregavel[] {
    return this.meuTcc ? ETAPAS_BY_TIPO[this.meuTcc.tipo_tcc] : [];
  }

  constructor(
    private readonly location: Location,
    private readonly painelService: PainelService,
    private readonly submissaoService: SubmissaoService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.carregarDados();
    this.etapaCtrl.valueChanges.subscribe(() => this.atualizarPrazo());
  }

  carregarDados(): void {
    this.isLoading = true;
    this.errorMessage = '';
    forkJoin({
      tcc: this.painelService.getMeuTcc(),
      cronograma: this.painelService.getCronogramaAtivo(),
    }).subscribe({
      next: ({ tcc, cronograma }) => {
        this.meuTcc = tcc;
        this.prazos = cronograma.aluno?.prazos ?? [];
        const etapas = ETAPAS_BY_TIPO[tcc.tipo_tcc];
        this.etapaCtrl.setValue(etapas[0] ?? null);
        this.atualizarPrazo();
        this.carregarHistorico();
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar os dados.');
        this.isLoading = false;
      },
    });
  }

  atualizarPrazo(): void {
    const etapa = this.etapaCtrl.value;
    if (!etapa || !this.prazos.length) {
      this.prazoSubmissao = null;
      return;
    }

    const etapaNormalizada = this.normalizarTexto(etapa);
    const prazo = this.prazos.find((item) => {
      const prazoNormalizado = this.normalizarTexto(item.nome_etapa);
      if (etapaNormalizada.includes('artigo') && prazoNormalizado.includes('artigo')) return true;
      return prazoNormalizado.includes(etapaNormalizada) || etapaNormalizada.includes(prazoNormalizado);
    });

    if (!prazo) {
      this.prazoSubmissao = null;
      return;
    }

    const [year, month, day] = prazo.data_limite.split('-').map(Number);
    this.prazoSubmissao = new Date(year, month - 1, day);
  }

  carregarHistorico(): void {
    this.submissaoService.listarSubmissoesEntregaveis().subscribe({
      next: (historico) => {
        this.historico = historico;
        this.isLoading = false;
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar o histórico de submissões.');
        this.isLoading = false;
      },
    });
  }

  onArtigoFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.arquivoFile = input.files[0];
    }
  }

  onComprovanteFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.comprovanteFile = input.files[0];
    }
  }

  removerArtigo(): void {
    this.arquivoFile = null;
    this.artigoInput.nativeElement.value = '';
  }

  removerComprovante(): void {
    this.comprovanteFile = null;
    this.comprovanteInput.nativeElement.value = '';
  }

  submeter(): void {
    if (!this.podeSubmeter || this.isSubmitting) return;
    this.isSubmitting = true;
    this.errorMessage = '';

    const formData = new FormData();
    formData.append('arquivo', this.arquivoFile!);
    if (this.etapaCtrl.value) {
      formData.append('etapa', this.etapaCtrl.value);
    }
    formData.append('foi_aceito', String(this.foiAceito));
    if (this.foiAceito && this.comprovanteFile) {
      formData.append('comprovante', this.comprovanteFile);
    }

    this.submissaoService.submeterEntregavel(formData).pipe(finalize(() => (this.isSubmitting = false))).subscribe({
      next: (res) => {
        this.isSubmitted = true;
        this.notaAtribuida = res.nota_automatica ?? null;
        this.carregarHistorico();
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Erro ao submeter. Tente novamente.');
      },
    });
  }

  visualizarArquivo(submissao: SubmissaoEntregavel): void {
    this.abrirArquivo(this.submissaoService.visualizarArquivo(submissao.id));
  }

  visualizarComprovante(submissao: SubmissaoEntregavel): void {
    this.abrirArquivo(this.submissaoService.visualizarComprovante(submissao.id));
  }

  cancelar(): void {
    void this.router.navigate(['/painel/aluno']);
  }

  voltar(): void {
    this.location.back();
  }

  formatarTamanho(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  formatarData(dateStr: string): string {
    return new Date(dateStr).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  private normalizarTexto(value: string): string {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();
  }

  private abrirArquivo(request: Observable<Blob>): void {
    this.errorMessage = '';
    request.subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank', 'noopener');
        window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
      },
      error: (error: unknown) => {
        this.errorMessage = getApiErrorMessage(error, 'Não foi possível abrir o arquivo.');
      },
    });
  }
}
