import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface TccPublico {
  id: string;
  titulo: string;
  tipo_tcc: 'Monografia' | 'Artigo' | 'Relatorio de Estagio';
  area_tematica: string;
  curso: string;
  aluno_nome: string;
  orientador_nome: string;
  data_defesa: string | null;
  banca: string[];
}

export interface DocumentoTcc {
  id: string;
  tipo: string;
  nome_arquivo: string;
  url_download: string;
  url_preview: string | null;
}

export interface TccPublicoDetalhe extends TccPublico {
  resumo: string | null;
  documentos: DocumentoTcc[];
}

export interface BuscarTccParams {
  area_tematica?: string;
  curso?: string;
  aluno?: string;
  titulo?: string;
}

@Injectable({ providedIn: 'root' })
export class PublicoService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  buscarTcc(params: BuscarTccParams): Observable<TccPublico[]> {
    let httpParams = new HttpParams();
    if (params.area_tematica) httpParams = httpParams.set('area_tematica', params.area_tematica);
    if (params.curso) httpParams = httpParams.set('curso', params.curso);
    if (params.aluno) httpParams = httpParams.set('aluno', params.aluno);
    if (params.titulo) httpParams = httpParams.set('titulo', params.titulo);
    return this.http.get<TccPublico[]>(`${this.api}/public/tcc`, { params: httpParams });
  }

  getDetalheTcc(id: string): Observable<TccPublicoDetalhe> {
    return this.http.get<TccPublicoDetalhe>(`${this.api}/public/tcc/${id}`);
  }
}
