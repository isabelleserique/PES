import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export type StatusDeposito =
  | 'AGUARDANDO_ENVIO'
  | 'EM_REVISAO'
  | 'DEVOLVIDO_PARA_CORRECAO'
  | 'APROVADO'
  | 'DEPOSITADO';

export type TipoDocumentoDeposito =
  | 'ATA_DEFESA'
  | 'FOLHA_APROVACAO'
  | 'FORMULARIOS'
  | 'DECLARACOES';

export interface DocumentoDeposito {
  id: string;
  tipo_documento: TipoDocumentoDeposito | 'TCC_FINAL';
  nome_arquivo: string;
  mime_type: string | null;
  tamanho_bytes: number;
  possui_preview: boolean;
  criado_em: string;
}

export interface DepositoResponse {
  id: string | null;
  tcc_id: string;
  aluno_id: string;
  aluno_nome: string;
  titulo_tcc: string;
  status: StatusDeposito;
  versao_final_nome: string | null;
  documentos: DocumentoDeposito[];
  observacao_revisao: string | null;
  submetido_em: string | null;
  atualizado_em: string | null;
}

@Injectable({ providedIn: 'root' })
export class DepositoService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  submeterDeposito(payload: FormData): Observable<DepositoResponse> {
    return this.http.post<DepositoResponse>(`${this.api}/biblioteca/deposito`, payload);
  }

  getMeuDeposito(): Observable<DepositoResponse> {
    return this.http.get<DepositoResponse>(`${this.api}/biblioteca/deposito/me`);
  }

  listarDepositos(): Observable<DepositoResponse[]> {
    return this.http.get<DepositoResponse[]>(`${this.api}/biblioteca/depositos`);
  }

  atualizarStatus(
    depositoId: string,
    payload: { status: StatusDeposito; observacao_revisao?: string | null },
  ): Observable<DepositoResponse> {
    return this.http.patch<DepositoResponse>(`${this.api}/biblioteca/deposito/${depositoId}/status`, payload);
  }

  visualizarDocumento(documentoId: string, preview = false): Observable<Blob> {
    return this.http.get(`${this.api}/biblioteca/deposito/documentos/${documentoId}/arquivo`, {
      params: preview ? { preview: 'true' } : {},
      responseType: 'blob',
    });
  }
}
