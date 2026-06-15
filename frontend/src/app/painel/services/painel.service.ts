import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface AuthenticatedUserProfile {
  id: string;
  nome_completo: string;
  email: string;
  username: string;
  perfil: 'COORDENADOR' | 'ALUNO' | 'ORIENTADOR';
  matricula: string | null;
  status: 'PENDENTE' | 'ATIVO' | 'REJEITADO';
  ativo: boolean;
}

export interface PendingRegistration {
  id: string;
  nome_completo: string;
  email: string;
  username: string;
  perfil: 'COORDENADOR' | 'ALUNO' | 'ORIENTADOR';
  matricula: string | null;
  status: 'PENDENTE' | 'ATIVO' | 'REJEITADO';
}

export interface ReviewRegistrationPayload {
  acao: 'APROVAR' | 'REJEITAR';
}

export interface ReviewRegistrationResponse {
  id: string;
  nome_completo: string;
  perfil: 'COORDENADOR' | 'ALUNO' | 'ORIENTADOR';
  status: 'PENDENTE' | 'ATIVO' | 'REJEITADO';
}

export type TipoTcc = 'Todos' | 'Monografia' | 'Artigo' | 'Relatorio de Estagio';
export type TipoTccAluno = Exclude<TipoTcc, 'Todos'>;
export type StatusTcc = 'AGUARDANDO_ACEITE' | 'EM_ANDAMENTO' | 'SEM_ORIENTADOR' | 'APROVADO' | 'REJEITADO';
export type StatusPrazo = 'A_VENCER' | 'PROXIMO' | 'HOJE' | 'VENCIDO';
export type CorPrazo = 'verde' | 'amarelo' | 'laranja' | 'vermelho';

export interface PeriodoResumo {
  id: string;
  nome: string;
  data_inicio: string;
  data_fim: string;
  ativo: boolean;
}

export interface CronogramaPrazo {
  id: string;
  nome_etapa: string;
  data_limite: string;
  tipo_tcc: TipoTcc;
  dias_restantes: number;
  status: StatusPrazo;
  cor: CorPrazo;
  mensagem: string;
  atrasado: boolean;
}

export interface CronogramaAluno {
  aluno_id: string;
  titulo_tcc: string | null;
  tipo_tcc: TipoTccAluno | null;
  status_tcc: StatusTcc | null;
  prazo_excedido: boolean;
  alerta_prazo: string | null;
  prazos: CronogramaPrazo[];
}

export interface CronogramaOrientando {
  aluno_id: string;
  aluno_nome: string;
  matricula: string | null;
  titulo_tcc: string;
  tipo_tcc: TipoTccAluno;
  status_tcc: StatusTcc;
  prazo_excedido: boolean;
  alerta_prazo: string | null;
  papel_orientacao: 'ORIENTADOR' | 'COORIENTADOR';
  prazos: CronogramaPrazo[];
}

export interface CronogramaPeriodoResponse {
  periodo: PeriodoResumo;
  perfil: 'COORDENADOR' | 'ALUNO' | 'ORIENTADOR';
  aluno: CronogramaAluno | null;
  orientandos: CronogramaOrientando[];
  filtro_orientando_id: string | null;
}

export interface TccPayload {
  titulo: string;
  tipo_tcc: TipoTccAluno;
  orientador_id: string;
  coorientador_id?: string;
}

export interface TccResponse {
  id: string;
  titulo: string;
  tipo_tcc: TipoTccAluno;
  orientador_id: string;
  orientador_nome: string;
  coorientador_id: string | null;
  coorientador_nome: string | null;
  periodo_id: string;
  periodo_nome: string;
  status: StatusTcc;
  prazo_excedido: boolean;
  alerta_prazo: string | null;
  observacao_orientador: string | null;
  criado_em: string;
  atualizado_em: string;
}

export interface OrientadorDisponivel {
  id: string;
  nome_completo: string;
  email: string;
}

export interface PendingOrientationRequest {
  tcc_id: string;
  aluno_id: string;
  aluno_nome: string;
  aluno_email: string;
  matricula: string | null;
  titulo: string;
  tipo_tcc: TipoTccAluno;
  status: StatusTcc;
  prazo_excedido: boolean;
  alerta_submissao_prazo: string | null;
  prazo_aceite: string | null;
  acao_fora_do_prazo: boolean;
  alerta_acao_prazo: string | null;
  criado_em: string;
}

export interface OrientationDecisionPayload {
  acao: 'ACEITAR' | 'RECUSAR';
  observacao?: string;
}

export interface OrientationDecisionResponse {
  tcc_id: string;
  aluno_id: string;
  aluno_nome: string;
  status: StatusTcc;
  observacao_orientador: string | null;
  acao_fora_do_prazo: boolean;
  alerta_acao_prazo: string | null;
}

export interface SessaoOrientacaoPayload {
  aluno_id: string;
  data_sessao: string;
  resumo: string;
  proximos_passos: string;
}

export interface SessaoOrientacao {
  id: string;
  tcc_id: string;
  aluno_id: string;
  aluno_nome: string;
  orientador_id: string;
  orientador_nome: string;
  data_sessao: string;
  resumo: string;
  proximos_passos: string;
  criado_em: string;
}

@Injectable({ providedIn: 'root' })
export class PainelService {
  private readonly api = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  getMeuPerfil(): Observable<AuthenticatedUserProfile> {
    return this.http.get<AuthenticatedUserProfile>(`${this.api}/usuarios/me`);
  }

  listarPendentes(): Observable<PendingRegistration[]> {
    return this.http.get<PendingRegistration[]>(`${this.api}/usuarios/pendentes`);
  }

  revisarCadastro(
    userId: string,
    payload: ReviewRegistrationPayload,
  ): Observable<ReviewRegistrationResponse> {
    return this.http.patch<ReviewRegistrationResponse>(`${this.api}/usuarios/${userId}/aprovar`, payload);
  }

  getCronogramaAtivo(orientandoId?: string): Observable<CronogramaPeriodoResponse> {
    return this.http.get<CronogramaPeriodoResponse>(`${this.api}/periodos/ativo/cronograma`, {
      params: orientandoId ? { orientando_id: orientandoId } : {},
    });
  }

  listarOrientadoresDisponiveis(): Observable<OrientadorDisponivel[]> {
    return this.http.get<OrientadorDisponivel[]>(`${this.api}/tcc/orientadores`);
  }

  getMeuTcc(): Observable<TccResponse> {
    return this.http.get<TccResponse>(`${this.api}/tcc/me`);
  }

  criarMeuTcc(payload: TccPayload): Observable<TccResponse> {
    return this.http.post<TccResponse>(`${this.api}/tcc/me`, payload);
  }

  atualizarMeuTcc(payload: TccPayload): Observable<TccResponse> {
    return this.http.patch<TccResponse>(`${this.api}/tcc/me`, payload);
  }

  listarSolicitacoesOrientacaoPendentes(): Observable<PendingOrientationRequest[]> {
    return this.http.get<PendingOrientationRequest[]>(`${this.api}/tcc/orientacoes/pendentes`);
  }

  decidirSolicitacaoOrientacao(
    tccId: string,
    payload: OrientationDecisionPayload,
  ): Observable<OrientationDecisionResponse> {
    return this.http.patch<OrientationDecisionResponse>(`${this.api}/tcc/orientacoes/${tccId}/decisao`, payload);
  }

  registrarSessaoOrientacao(payload: SessaoOrientacaoPayload): Observable<SessaoOrientacao> {
    return this.http.post<SessaoOrientacao>(`${this.api}/orientacoes/sessoes`, payload);
  }

  listarSessoesOrientador(alunoId: string): Observable<SessaoOrientacao[]> {
    return this.http.get<SessaoOrientacao[]>(`${this.api}/orientacoes/sessoes`, {
      params: { aluno_id: alunoId },
    });
  }

  listarMinhasSessoes(): Observable<SessaoOrientacao[]> {
    return this.http.get<SessaoOrientacao[]>(`${this.api}/tcc/me/sessoes`);
  }
}
