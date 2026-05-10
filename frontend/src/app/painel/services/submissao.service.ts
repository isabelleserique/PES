import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface SubmissaoArtigo {
  id: string;
  versao: number;
  nome_arquivo: string;
  data_submissao: string;
  fora_do_prazo: boolean;
  foi_aceito: boolean;
  nome_comprovante?: string;
}

export interface SubmissaoArtigoResponse {
  id: string;
  versao: number;
  mensagem: string;
  nota_automatica?: number;
}

@Injectable({ providedIn: 'root' })
export class SubmissaoService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  submeterArtigo(payload: FormData): Observable<SubmissaoArtigoResponse> {
    return this.http.post<SubmissaoArtigoResponse>(`${this.api}/submissoes/artigo`, payload);
  }

  listarSubmissoesArtigo(): Observable<SubmissaoArtigo[]> {
    return this.http.get<SubmissaoArtigo[]>(`${this.api}/submissoes/artigo`);
  }
}
