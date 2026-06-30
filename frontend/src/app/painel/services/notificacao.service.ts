import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface PreferenciasNotificacao {
  email_prazos_orientandos: boolean;
  antecedencia_dias: number;
  email_notas_parciais: boolean;
  email_notas_finais: boolean;
}

@Injectable({ providedIn: 'root' })
export class NotificacaoService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  getPreferencias(): Observable<PreferenciasNotificacao> {
    return this.http.get<PreferenciasNotificacao>(`${this.api}/notificacoes/preferencias`);
  }

  salvarPreferencias(payload: PreferenciasNotificacao): Observable<PreferenciasNotificacao> {
    return this.http.put<PreferenciasNotificacao>(`${this.api}/notificacoes/preferencias`, payload);
  }
}
