import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface ConsentimentoLgpd {
  publicar_portal_publico: boolean;
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
