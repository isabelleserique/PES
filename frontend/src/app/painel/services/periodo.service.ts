import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export type TipoDeTCC = 'Todos' | 'Monografia' | 'Artigo' | 'Relatorio de Estagio';

export interface PrazoPayload {
  nome_etapa: string;
  data_limite: string;
  tipo_tcc: TipoDeTCC;
}

export interface CreatePeriodoPayload {
  nome: string;
  data_inicio: string;
  data_fim: string;
  ativo: boolean;
  prazos: PrazoPayload[];
}

export interface UpdatePeriodoPayload {
  nome?: string;
  data_inicio?: string;
  data_fim?: string;
  ativo?: boolean;
  prazos?: PrazoPayload[];
}

export interface PrazoResponse {
  id: string;
  nome_etapa: string;
  data_limite: string;
  tipo_tcc: TipoDeTCC;
}

export interface PeriodoResponse {
  id: string;
  nome: string;
  data_inicio: string;
  data_fim: string;
  ativo: boolean;
  prazos: PrazoResponse[];
}

@Injectable({ providedIn: 'root' })
export class PeriodoService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  criarPeriodo(payload: CreatePeriodoPayload): Observable<PeriodoResponse> {
    return this.http.post<PeriodoResponse>(`${this.api}/periodos`, payload);
  }

  listarPeriodos(): Observable<PeriodoResponse[]> {
    return this.http.get<PeriodoResponse[]>(`${this.api}/periodos`);
  }

  getPeriodoById(periodoId: string): Observable<PeriodoResponse> {
    return this.http.get<PeriodoResponse>(`${this.api}/periodos/${periodoId}`);
  }

  atualizarPeriodo(periodoId: string, payload: UpdatePeriodoPayload): Observable<PeriodoResponse> {
    return this.http.patch<PeriodoResponse>(`${this.api}/periodos/${periodoId}`, payload);
  }
}
