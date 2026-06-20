import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface ConsentimentoLgpd {
  // Consentimento para exibir dados do TCC no portal público (apenas finalizados/aprovados)
  publicar_portal_publico: boolean;
  // Consentimento para compartilhamento de dados pessoais com terceiros
  compartilhar_terceiros: boolean;
  atualizado_em: string | null;
}

@Injectable({ providedIn: 'root' })
export class PrivacidadeService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  getConsentimento(): Observable<ConsentimentoLgpd> {
    return this.http.get<ConsentimentoLgpd>(`${this.api}/privacidade/consentimento`);
  }

  salvarConsentimento(payload: ConsentimentoLgpd): Observable<ConsentimentoLgpd> {
    return this.http.put<ConsentimentoLgpd>(`${this.api}/privacidade/consentimento`, payload);
  }
}
