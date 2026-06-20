import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export type StatusDeposito =
  | 'AGUARDANDO_ENVIO'
  | 'EM_REVISAO'
  | 'DEVOLVIDO_CORRECAO'
  | 'APROVADO'
  | 'DEPOSITADO';

export type TipoDocumentoDeposito =
  | 'ATA_DEFESA'
  | 'FOLHA_APROVACAO'
  | 'FORMULARIOS'
  | 'DECLARACOES';

export interface DocumentoDeposito {
  tipo: TipoDocumentoDeposito;
  nome_arquivo: string;
  enviado_em: string;
}

export interface DepositoResponse {
  id: string;
  aluno_id: string;
  aluno_nome: string;
  titulo_tcc: string;
  status: StatusDeposito;
  versao_final_nome: string | null;
  documentos: DocumentoDeposito[];
  observacao_revisao: string | null;
  atualizado_em: string;
}

@Injectable({ providedIn: 'root' })
export class DepositoService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  // US026 + US027 + US051 — versão final + documentos obrigatórios (multipart)
  submeterDeposito(payload: FormData): Observable<DepositoResponse> {
    return this.http.post<DepositoResponse>(`${this.api}/biblioteca/deposito`, payload);
  }

  // US028 — status do depósito do usuário atual
  getMeuDeposito(): Observable<DepositoResponse | null> {
    return this.http.get<DepositoResponse | null>(`${this.api}/biblioteca/deposito/me`);
  }
}
