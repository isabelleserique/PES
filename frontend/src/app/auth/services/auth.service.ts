import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface LoginPayload {
  username: string;
  senha: string;
}

export interface CadastroPayload {
  perfil: string;
  nome_completo: string;
  email: string;
  username: string;
  senha: string;
}

export interface EsqueceuSenhaPayload {
  email: string;
}

export interface RedefinirSenhaPayload {
  nova_senha: string;
  confirmar_senha: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  login(payload: LoginPayload): Observable<unknown> {
    return this.http.post(`${this.api}/auth/login`, payload);
  }

  cadastrar(payload: CadastroPayload): Observable<unknown> {
    return this.http.post(`${this.api}/auth/cadastro`, payload);
  }

  esqueceuSenha(payload: EsqueceuSenhaPayload): Observable<unknown> {
    return this.http.post(`${this.api}/auth/esqueceu-senha`, payload);
  }

  redefinirSenha(payload: RedefinirSenhaPayload): Observable<unknown> {
    return this.http.post(`${this.api}/auth/redefinir-senha`, payload);
  }
}
