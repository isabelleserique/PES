import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Router } from '@angular/router';

import { SubmissaoArtigo, SubmissaoService } from '../../services/submissao.service';

@Component({
  selector: 'app-submeter-artigo',
  templateUrl: './submeter-artigo.component.html',
  styleUrls: ['./submeter-artigo.component.css'],
})
export class SubmeterArtigoComponent implements OnInit {
  @ViewChild('artigoInput') artigoInput!: ElementRef<HTMLInputElement>;
  @ViewChild('comprovanteInput') comprovanteInput!: ElementRef<HTMLInputElement>;

  artigoFile: File | null = null;
  comprovanteFile: File | null = null;
  readonly foiAceitoCtrl = new FormControl(false);

  isSubmitting = false;
  isSubmitted = false;
  isLoading = true;
  errorMessage = '';
  notaAtribuida: number | null = null;

  prazoSubmissao: Date | null = null;
  historico: SubmissaoArtigo[] = [];

  get foiAceito(): boolean {
    return !!this.foiAceitoCtrl.value;
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
    if (!this.artigoFile) return false;
    if (this.foiAceito && !this.comprovanteFile) return false;
    return true;
  }

  constructor(
    private readonly submissaoService: SubmissaoService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.carregarHistorico();
  }

  carregarHistorico(): void {
    this.isLoading = true;
    this.submissaoService.listarSubmissoesArtigo().subscribe({
      next: (historico) => {
        this.historico = historico;
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  onArtigoFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.artigoFile = input.files[0];
    }
  }

  onComprovanteFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.comprovanteFile = input.files[0];
    }
  }

  removerArtigo(): void {
    this.artigoFile = null;
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
    formData.append('artigo', this.artigoFile!);
    formData.append('foi_aceito', String(this.foiAceito));
    if (this.foiAceito && this.comprovanteFile) {
      formData.append('comprovante', this.comprovanteFile);
    }

    this.submissaoService.submeterArtigo(formData).subscribe({
      next: (res) => {
        this.isSubmitting = false;
        this.isSubmitted = true;
        this.notaAtribuida = res.nota_automatica ?? null;
      },
      error: () => {
        this.isSubmitting = false;
        this.errorMessage = 'Erro ao submeter o artigo. Tente novamente.';
      },
    });
  }

  cancelar(): void {
    void this.router.navigate(['/painel/aluno']);
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
}
