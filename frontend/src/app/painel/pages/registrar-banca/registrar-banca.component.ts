import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { finalize } from 'rxjs/operators';

import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import {
  BancaService,
  ComposicaoBancaPayload,
  MembroBanca,
  PapelBanca,
  TitulacaoMembro,
} from '../../services/banca.service';
import { CronogramaOrientando, PainelService } from '../../services/painel.service';

@Component({
  selector: 'app-registrar-banca',
  templateUrl: './registrar-banca.component.html',
  styleUrls: ['./registrar-banca.component.css'],
})
export class RegistrarBancaComponent implements OnInit {
  isLoading = true;
  isSaving = false;
  errorMessage = '';
  successMessage = '';

  orientandos: CronogramaOrientando[] = [];
  orientandoSelecionado: CronogramaOrientando | null = null;

  readonly titulacoes: TitulacaoMembro[] = ['Especialista', 'Mestre', 'Doutor', 'Pós-Doutorado'];
  readonly papeis: { value: PapelBanca; label: string }[] = [
    { value: 'AVALIADOR_INTERNO', label: 'Avaliador interno' },
    { value: 'AVALIADOR_EXTERNO', label: 'Avaliador externo' },
    { value: 'SUPLENTE', label: 'Suplente' },
    { value: 'ORIENTADOR', label: 'Orientador' },
    { value: 'COORIENTADOR', label: 'Coorientador' },
  ];

  readonly bancaForm = this.fb.group({
    aluno_id: ['', Validators.required],
    data_defesa: [null as Date | null, Validators.required],
    horario_defesa: ['', Validators.required],
    local_defesa: ['', [Validators.required, Validators.maxLength(160)]],
    membros: this.fb.array([
      this.criarMembro('AVALIADOR_INTERNO'),
      this.criarMembro('AVALIADOR_EXTERNO'),
      this.criarMembro('SUPLENTE'),
    ]),
  });

  constructor(
    private readonly fb: FormBuilder,
    private readonly location: Location,
    private readonly painelService: PainelService,
    private readonly bancaService: BancaService,
  ) {}

  get membros() {
    return this.bancaForm.controls.membros;
  }

  ngOnInit(): void {
    this.carregarOrientandos();

    this.bancaForm.controls.aluno_id.valueChanges.subscribe((alunoId) => {
      this.orientandoSelecionado = this.orientandos.find((orientando) => orientando.aluno_id === alunoId) ?? null;
      this.successMessage = '';
    });
  }

  criarMembro(papel: PapelBanca = 'AVALIADOR_INTERNO'): FormGroup {
    return this.fb.group({
      nome: ['', [Validators.required, Validators.maxLength(120)]],
      titulacao: ['Doutor' as TitulacaoMembro, Validators.required],
      instituicao: ['', [Validators.required, Validators.maxLength(120)]],
      papel: [papel, Validators.required],
    });
  }

  adicionarMembro(): void {
    this.membros.push(this.criarMembro());
  }

  removerMembro(index: number): void {
    if (this.membros.length <= 2) return;
    this.membros.removeAt(index);
  }

  registrar(): void {
    this.bancaForm.markAllAsTouched();
    if (this.bancaForm.invalid || this.isSaving) return;

    const raw = this.bancaForm.getRawValue();
    const dataObj = raw.data_defesa as Date;
    const data = `${dataObj.getFullYear()}-${String(dataObj.getMonth() + 1).padStart(2, '0')}-${String(dataObj.getDate()).padStart(2, '0')}`;
    const horario = raw.horario_defesa || '00:00';

    const membros: MembroBanca[] = (raw.membros ?? []).map((membro) => ({
      nome: (membro['nome'] ?? '').trim(),
      titulacao: membro['titulacao'] as TitulacaoMembro,
      instituicao: (membro['instituicao'] ?? '').trim(),
      papel: membro['papel'] as PapelBanca,
    }));

    const payload: ComposicaoBancaPayload = {
      aluno_id: raw.aluno_id ?? '',
      data_defesa: `${data}T${horario}:00`,
      local: (raw.local_defesa ?? '').trim(),
      membros,
    };

    this.isSaving = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.bancaService
      .registrarBanca(payload)
      .pipe(finalize(() => (this.isSaving = false)))
      .subscribe({
        next: (response) => {
          this.successMessage = `Composição da banca de ${response.aluno_nome} registrada com sucesso.`;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível registrar a composição da banca.');
        },
      });
  }

  voltar(): void {
    this.location.back();
  }

  private carregarOrientandos(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.painelService
      .getCronogramaAtivo()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (cronograma) => {
          this.orientandos = cronograma.orientandos ?? [];
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível carregar os orientandos.');
        },
      });
  }
}
