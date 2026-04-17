import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface AuthenticatedUserProfile {
  id: string;
  nome_completo: string;
  email: string;
  username: string;
  perfil: 'COORDENADOR' | 'ALUNO' | 'ORIENTADOR';
  matricula: string | null;
  status: 'PENDENTE' | 'ATIVO' | 'REJEITADO';
  ativo: boolean;
}

export interface PendingRegistration {
  id: string;
  nome_completo: string;
  email: string;
  username: string;
  perfil: 'COORDENADOR' | 'ALUNO' | 'ORIENTADOR';
  matricula: string | null;
  status: 'PENDENTE' | 'ATIVO' | 'REJEITADO';
}

export interface ReviewRegistrationPayload {
  acao: 'APROVAR' | 'REJEITAR';
}

export interface ReviewRegistrationResponse {
  id: string;
  nome_completo: string;
  perfil: 'COORDENADOR' | 'ALUNO' | 'ORIENTADOR';
  status: 'PENDENTE' | 'ATIVO' | 'REJEITADO';
}

@Injectable({ providedIn: 'root' })
export class PainelService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  getMeuPerfil(): Observable<AuthenticatedUserProfile> {
    return this.http.get<AuthenticatedUserProfile>(`${this.api}/usuarios/me`);
  }

  listarPendentes(): Observable<PendingRegistration[]> {
    return this.http.get<PendingRegistration[]>(`${this.api}/usuarios/pendentes`);
  }

  revisarCadastro(
    userId: string,
    payload: ReviewRegistrationPayload,
  ): Observable<ReviewRegistrationResponse> {
    return this.http.patch<ReviewRegistrationResponse>(`${this.api}/usuarios/${userId}/aprovar`, payload);
  }
}
