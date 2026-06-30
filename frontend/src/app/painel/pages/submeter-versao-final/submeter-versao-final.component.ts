import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { PainelService, TccResponse } from '../../services/painel.service';
import { DepositoService, TipoDocumentoDeposito } from '../../services/deposito.service';

const MAX_FILE_SIZE_MB = 50;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

interface DocumentoSlot {
  tipo: TipoDocumentoDeposito;
  fieldName: string;
  label: string;
  descricao: string;
  file: File | null;
}

@Component({
  selector: 'app-submeter-versao-final',
  templateUrl: './submeter-versao-final.component.html',
  styleUrls: ['./submeter-versao-final.component.css'],
})
export class SubmeterVersaoFinalComponent implements OnInit {
  isLoading = true;
  isSubmitting = false;
  isSubmitted = false;
  errorMessage = '';
  fileSizeError = '';

  meuTcc: TccResponse | null = null;
  versaoFinalFile: File | null = null;

  readonly maxFileSizeMb = MAX_FILE_SIZE_MB;
  readonly formatosAceitos = '.pdf,.docx';

  readonly documentos: DocumentoSlot[] = [
    {
      tipo: 'ATA_DEFESA',
      fieldName: 'documento_ata_defesa',
      label: 'Ata de defesa',
      descricao: 'Documento gerado após a defesa.',
      file: null,
    },
    {
      tipo: 'FOLHA_APROVACAO',
      fieldName: 'documento_folha_aprovacao',
      label: 'Folha de aprovação assinada',
      descricao: 'Assinada pela banca.',
      file: null,
    },
    {
      tipo: 'FORMULARIOS',
      fieldName: 'documento_formularios',
      label: 'Formulários',
      descricao: 'Formulários institucionais exigidos.',
      file: null,
    },
    {
      tipo: 'DECLARACOES',
      fieldName: 'documento_declaracoes',
      label: 'Declarações',
      descricao: 'Declarações obrigatórias.',
      file: null,
    },
  ];

  constructor(
    private readonly location: Location,
    private readonly router: Router,
    private readonly painelService: PainelService,
    private readonly depositoService: DepositoService,
  ) {}

  ngOnInit(): void {
    this.carregarTcc();
  }

  get documentosPendentes(): DocumentoSlot[] {
    return this.documentos.filter((documento) => !documento.file);
  }

  get podeSubmeter(): boolean {
    return !!this.versaoFinalFile && this.documentosPendentes.length === 0;
  }

  onVersaoFinalChange(event: Event): void {
    const file = this.extrairArquivo(event, 'A versão final');
    if (file) this.versaoFinalFile = file;
  }

  removerVersaoFinal(): void {
    this.versaoFinalFile = null;
  }

  onDocumentoChange(event: Event, slot: DocumentoSlot): void {
    const file = this.extrairArquivo(event, slot.label);
    if (file) slot.file = file;
  }

  removerDocumento(slot: DocumentoSlot): void {
    slot.file = null;
  }

  submeter(): void {
    if (!this.podeSubmeter || this.isSubmitting) return;

    this.isSubmitting = true;
    this.errorMessage = '';

    const formData = new FormData();
    formData.append('versao_final', this.versaoFinalFile!);
    this.documentos.forEach((documento) => {
      if (documento.file) {
        formData.append(documento.fieldName, documento.file);
      }
    });

    this.depositoService
      .submeterDeposito(formData)
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: () => {
          this.isSubmitted = true;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível submeter o depósito. Tente novamente.');
        },
      });
  }

  irParaStatus(): void {
    void this.router.navigate(['/painel/status-deposito']);
  }

  voltar(): void {
    this.location.back();
  }

  formatarTamanho(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  private extrairArquivo(event: Event, rotulo: string): File | null {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return null;

    const file = input.files[0];
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx'].includes(extension ?? '')) {
      this.fileSizeError = `${rotulo} deve estar em PDF ou DOCX.`;
      input.value = '';
      return null;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      this.fileSizeError = `${rotulo} excede o limite de ${MAX_FILE_SIZE_MB} MB (${this.formatarTamanho(file.size)}).`;
      input.value = '';
      return null;
    }
    this.fileSizeError = '';
    return file;
  }

  private carregarTcc(): void {
    this.isLoading = true;
    this.painelService
      .getMeuTcc()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (tcc) => {
          this.meuTcc = tcc;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar os dados do seu TCC.');
        },
      });
  }
}
