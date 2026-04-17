import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

const AUTH_SESSION_STORAGE_KEY = 'tccomp.auth.session';

export interface LoginPayload {
  email: string;
  senha: string;
}

export interface AuthenticatedUser {
  id: string;
  nome_completo: string;
  email: string;
  perfil: 'COORDENADOR' | 'ALUNO' | 'ORIENTADOR';
}

export type UserPerfil = AuthenticatedUser['perfil'];

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: AuthenticatedUser;
}

export type CadastroPerfil = 'ALUNO' | 'ORIENTADOR';

export interface CadastroPayload {
  perfil: CadastroPerfil;
  nome_completo: string;
  email: string;
  username: string;
  senha: string;
  matricula?: string;
}

export interface EsqueceuSenhaPayload {
  email: string;
}

export interface MessageResponse {
  mensagem: string;
}

export interface CadastroResponse extends MessageResponse {
  id: string;
  nome_completo: string;
  status: 'PENDENTE' | 'ATIVO' | 'REJEITADO';
}

export interface RedefinirSenhaPayload {
  token: string;
  nova_senha: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  login(payload: LoginPayload): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.api}/auth/login`, payload)
      .pipe(tap((session) => this.storeSession(session)));
  }

  cadastrar(payload: CadastroPayload): Observable<CadastroResponse> {
    return this.http.post<CadastroResponse>(`${this.api}/usuarios/solicitar-cadastro`, payload);
  }

  esqueceuSenha(payload: EsqueceuSenhaPayload): Observable<MessageResponse> {
    return this.http.post<MessageResponse>(`${this.api}/auth/solicitar-reset`, payload);
  }

  redefinirSenha(payload: RedefinirSenhaPayload): Observable<MessageResponse> {
    return this.http.post<MessageResponse>(`${this.api}/auth/confirmar-reset`, payload);
  }

  getStoredSession(): LoginResponse | null {
    const rawSession = localStorage.getItem(AUTH_SESSION_STORAGE_KEY);
    if (!rawSession) {
      return null;
    }

    try {
      const session = JSON.parse(rawSession) as LoginResponse;
      if (!this.isSessionStillValid(session)) {
        this.clearSession();
        return null;
      }

      return session;
    } catch {
      this.clearSession();
      return null;
    }
  }

  isAuthenticated(): boolean {
    return this.getStoredSession() !== null;
  }

  getAccessToken(): string | null {
    return this.getStoredSession()?.access_token ?? null;
  }

  getStoredUser(): AuthenticatedUser | null {
    return this.getStoredSession()?.user ?? null;
  }

  getStoredPerfil(): UserPerfil | null {
    return this.getStoredUser()?.perfil ?? null;
  }

  clearSession(): void {
    localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  }

  getPostLoginRoute(): string[] {
    const perfil = this.getStoredPerfil();

    switch (perfil) {
      case 'COORDENADOR':
        return ['/painel/coordenador'];
      case 'ALUNO':
        return ['/painel/aluno'];
      case 'ORIENTADOR':
        return ['/painel/orientador'];
      default:
        return ['/auth/login'];
    }
  }

  private storeSession(session: LoginResponse): void {
    localStorage.setItem(AUTH_SESSION_STORAGE_KEY, JSON.stringify(session));
  }

  private isSessionStillValid(session: LoginResponse): boolean {
    const expiresAt = Date.parse(session.expires_at);
    return Number.isFinite(expiresAt) && expiresAt > Date.now();
  }
}
