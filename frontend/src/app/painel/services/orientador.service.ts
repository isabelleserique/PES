import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface SolicitacaoOrientacao {
  id: string;
  nomeAluno: string;
  tituloDeTCC: string;
  tipo: string;
  status: 'PENDENTE' | 'ACEITO' | 'RECUSADO';
}

export interface ResponderSolicitacaoPayload {
  acao: 'ACEITAR' | 'REJEITAR';
  observacao: string;
  status_tcc: string;
}

@Injectable({ providedIn: 'root' })
export class OrientadorService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  listarSolicitacoes(): Observable<SolicitacaoOrientacao[]> {
    return this.http.get<SolicitacaoOrientacao[]>(`${this.api}/orientador/solicitacoes`);
  }

  responderSolicitacao(id: string, payload: ResponderSolicitacaoPayload): Observable<void> {
    return this.http.patch<void>(`${this.api}/orientador/solicitacoes/${id}`, payload);
  }
}
