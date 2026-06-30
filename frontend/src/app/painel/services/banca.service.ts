import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export type PapelBanca =
  | 'ORIENTADOR'
  | 'COORIENTADOR'
  | 'AVALIADOR_INTERNO'
  | 'AVALIADOR_EXTERNO'
  | 'SUPLENTE';

export type TitulacaoMembro = 'Especialista' | 'Mestre' | 'Doutor' | 'Pós-Doutorado';

export interface MembroBanca {
  nome: string;
  titulacao: TitulacaoMembro | string;
  instituicao: string;
  papel: PapelBanca;
}

export interface ComposicaoBancaPayload {
  aluno_id: string;
  data_defesa: string;
  local: string;
  membros: MembroBanca[];
}

export interface ComposicaoBancaResponse {
  id: string;
  tcc_id: string;
  aluno_id: string;
  aluno_nome: string;
  data_defesa: string;
  local: string;
  membros: MembroBanca[];
  criado_em: string;
  atualizado_em: string;
}

@Injectable({ providedIn: 'root' })
export class BancaService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  registrarBanca(payload: ComposicaoBancaPayload): Observable<ComposicaoBancaResponse> {
    return this.http.post<ComposicaoBancaResponse>(`${this.api}/defesas/banca`, payload);
  }

  getBancaDoAluno(alunoId?: string): Observable<ComposicaoBancaResponse | null> {
    return this.http.get<ComposicaoBancaResponse | null>(`${this.api}/defesas/banca`, {
      params: alunoId ? { aluno_id: alunoId } : {},
    });
  }
}
