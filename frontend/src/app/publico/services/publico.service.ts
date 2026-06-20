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

export interface ProfessorPublico {
  id: string;
  nome: string;
  titulacao: string;
  area_atuacao: string;
  instituicao: string;
  total_orientacoes: number;
}

export interface TccOrientadoPublico {
  id: string;
  titulo: string;
  tipo_tcc: 'Monografia' | 'Artigo' | 'Relatorio de Estagio';
  ano: number | null;
  aluno_nome: string;
}

export interface ProfessorPublicoDetalhe extends ProfessorPublico {
  email: string | null;
  lattes_url: string | null;
  bio: string | null;
  areas: string[];
  tccs_orientados: TccOrientadoPublico[];
}

export interface BuscarProfessoresParams {
  nome?: string;
  area?: string;
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

  buscarProfessores(params: BuscarProfessoresParams): Observable<ProfessorPublico[]> {
    let httpParams = new HttpParams();
    if (params.nome) httpParams = httpParams.set('nome', params.nome);
    if (params.area) httpParams = httpParams.set('area', params.area);
    return this.http.get<ProfessorPublico[]>(`${this.api}/public/professores`, { params: httpParams });
  }

  getDetalheProfessor(id: string): Observable<ProfessorPublicoDetalhe> {
    return this.http.get<ProfessorPublicoDetalhe>(`${this.api}/public/professores/${id}`);
  }
}
