import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';

export interface Professor {
  id: string;
  nome: string;
  area: string;
}

@Component({
  selector: 'app-definir-tcc',
  templateUrl: './definir-tcc.component.html',
  styleUrls: ['./definir-tcc.component.css'],
})
export class DefinirTccComponent {
  readonly step1Form = this.fb.group({
    titulo: ['', Validators.required],
    tipoDeTCC: ['', Validators.required],
    resumo: ['', Validators.required],
  });

  readonly step2Form = this.fb.group({
    orientadorId: ['', Validators.required],
  });

  readonly step3Form = this.fb.group({
    coorientadorId: [''],
  });

  readonly tiposDeTCC = ['Monografia', 'Relatório de Estágio', 'Artigo Científico'];

  professores: Professor[] = [];
  isLoadingProfessores = false;

  searchOrientador = '';
  searchCoorientador = '';
  orientadorSelecionado: Professor | null = null;
  coorientadorSelecionado: Professor | null = null;

  isSubmitting = false;
  isSubmitted = false;
  errorMessage = '';

  prazoDefinicao: Date | null = null;

  get foraDoPrazo(): boolean {
    if (!this.prazoDefinicao) return false;
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    return hoje > this.prazoDefinicao;
  }

  get diasAtraso(): number {
    if (!this.prazoDefinicao) return 0;
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    return Math.ceil((hoje.getTime() - this.prazoDefinicao.getTime()) / (1000 * 60 * 60 * 24));
  }

  get professoresFiltrados(): Professor[] {
    const q = this.searchOrientador.toLowerCase();
    if (!q) return this.professores;
    return this.professores.filter(
      (p) => p.nome.toLowerCase().includes(q) || p.area.toLowerCase().includes(q),
    );
  }

  get coorientadoresFiltrados(): Professor[] {
    const base = this.orientadorSelecionado
      ? this.professores.filter((p) => p.id !== this.orientadorSelecionado!.id)
      : this.professores;
    const q = this.searchCoorientador.toLowerCase();
    if (!q) return base;
    return base.filter(
      (p) => p.nome.toLowerCase().includes(q) || p.area.toLowerCase().includes(q),
    );
  }

  constructor(
    private readonly fb: FormBuilder,
    private readonly router: Router,
  ) {}

  selecionarOrientador(prof: Professor): void {
    this.orientadorSelecionado = prof;
    this.step2Form.patchValue({ orientadorId: prof.id });
  }

  selecionarCoorientador(prof: Professor): void {
    this.coorientadorSelecionado = prof;
    this.step3Form.patchValue({ coorientadorId: prof.id });
  }

  limparCoorientador(): void {
    this.coorientadorSelecionado = null;
    this.step3Form.patchValue({ coorientadorId: '' });
  }

  onSearchOrientador(event: Event): void {
    this.searchOrientador = (event.target as HTMLInputElement).value;
  }

  onSearchCoorientador(event: Event): void {
    this.searchCoorientador = (event.target as HTMLInputElement).value;
  }

  submeter(): void {
    if (this.isSubmitting || this.isSubmitted) return;
    this.isSubmitting = true;
    this.errorMessage = '';

    this.isSubmitting = false;
  }

  cancelar(): void {
    void this.router.navigate(['/painel/aluno']);
  }
}
