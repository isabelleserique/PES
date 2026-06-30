import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export type EtapaEntregavel =
  | 'Revisão Bibliográfica'
  | '1ª Entrega'
  | '2ª Entrega'
  | 'Monografia Final'
  | '1º Entregável intermediário'
  | '2º Entregável intermediário'
  | 'Relatório Final'
  | 'Artigo Final';

export interface SubmissaoEntregavel {
  id: string;
  tipo_tcc: string;
  etapa: EtapaEntregavel;
  versao: number;
  ultima_versao: boolean;
  nome_arquivo: string;
  data_submissao: string;
  fora_do_prazo: boolean;
  foi_aceito: boolean;
  nome_comprovante?: string;
  nota_automatica?: number | null;
}

export interface SubmissaoEntregavelResponse {
  id: string;
  tipo_tcc: string;
  etapa: EtapaEntregavel;
  versao: number;
  mensagem: string;
  nota_automatica?: number;
}

export interface SubmissaoHistorico {
  id: string;
  aluno_id: string;
  aluno_nome: string;
  matricula: string | null;
  tcc_id: string;
  titulo_tcc: string;
  tipo_tcc: string;
  etapa: string;
  versao: number;
  ultima_versao: boolean;
  nome_arquivo: string;
  data_submissao: string;
  fora_do_prazo: boolean;
  foi_aceito: boolean;
  nome_comprovante: string | null;
  nota_automatica: number | null;
}

export interface SubmissaoAtrasada {
  id: string;
  aluno_id: string;
  aluno_nome: string;
  matricula: string | null;
  tcc_id: string;
  titulo_tcc: string;
  tipo_tcc: string;
  etapa: string;
  versao: number;
  nome_arquivo: string;
  data_limite: string;
  data_submissao: string;
  dias_atraso: number;
}

export interface LogAtividade {
  id: string;
  usuario_nome: string;
  usuario_email: string;
  usuario_perfil: string;
  acao: string;
  entidade: string | null;
  descricao: string;
  criado_em: string;
}

export interface ApresentacaoArtigoPayload {
  data_apresentacao: string;
  tipo_veiculo?: string | null;
  veiculo_publicacao?: string | null;
  local_apresentacao?: string | null;
  observacoes?: string | null;
}

export interface ApresentacaoArtigo {
  id: string;
  tcc_id: string;
  submissao_id: string | null;
  data_apresentacao: string;
  tipo_veiculo: string | null;
  veiculo_publicacao: string | null;
  local_apresentacao: string | null;
  observacoes: string | null;
  artigo_ja_aceito: boolean;
  criado_em: string;
}

@Injectable({ providedIn: 'root' })
export class SubmissaoService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  submeterEntregavel(payload: FormData): Observable<SubmissaoEntregavelResponse> {
    return this.http.post<SubmissaoEntregavelResponse>(`${this.api}/submissoes/entregaveis`, payload);
  }

  listarSubmissoesEntregaveis(): Observable<SubmissaoEntregavel[]> {
    return this.http.get<SubmissaoEntregavel[]>(`${this.api}/submissoes/entregaveis`);
  }

  listarHistoricoSubmissoes(): Observable<SubmissaoHistorico[]> {
    return this.http.get<SubmissaoHistorico[]>(`${this.api}/submissoes/historico`);
  }

  listarHistoricoOrientador(): Observable<SubmissaoHistorico[]> {
    return this.http.get<SubmissaoHistorico[]>(`${this.api}/submissoes/orientador`);
  }

  listarSubmissoesAtrasadas(): Observable<SubmissaoAtrasada[]> {
    return this.http.get<SubmissaoAtrasada[]>(`${this.api}/submissoes/atrasadas`);
  }

  listarLogsAtividade(): Observable<LogAtividade[]> {
    return this.http.get<LogAtividade[]>(`${this.api}/logs`);
  }

  registrarApresentacaoArtigo(payload: ApresentacaoArtigoPayload): Observable<ApresentacaoArtigo> {
    return this.http.post<ApresentacaoArtigo>(`${this.api}/submissoes/apresentacao-artigo`, payload);
  }

  listarMinhasApresentacoes(): Observable<ApresentacaoArtigo[]> {
    return this.http.get<ApresentacaoArtigo[]>(`${this.api}/submissoes/apresentacao-artigo`);
  }

  visualizarArquivo(submissaoId: string): Observable<Blob> {
    return this.http.get(`${this.api}/submissoes/entregaveis/${submissaoId}/arquivo`, {
      responseType: 'blob',
    });
  }

  visualizarComprovante(submissaoId: string): Observable<Blob> {
    return this.http.get(`${this.api}/submissoes/entregaveis/${submissaoId}/comprovante`, {
      responseType: 'blob',
    });
  }
}
