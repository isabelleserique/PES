import { Component } from '@angular/core';

import { AuthService, UserPerfil } from '../../../auth/services/auth.service';

interface PainelNavLink {
  label: string;
  path: string;
  shortLabel?: string;
  primary?: boolean;
}

@Component({
  selector: 'app-painel-nav',
  templateUrl: './painel-nav.component.html',
  styleUrls: ['./painel-nav.component.css'],
})
export class PainelNavComponent {
  readonly perfil = this.authService.getStoredPerfil();
  readonly links = this.buildLinks(this.perfil);
  readonly primaryLinks = this.links.filter((link) => link.primary);
  readonly overflowLinks = this.links.filter((link) => !link.primary);
  readonly perfilLabel = this.getPerfilLabel(this.perfil);

  constructor(private readonly authService: AuthService) {}

  private getPerfilLabel(perfil: UserPerfil | null): string {
    switch (perfil) {
      case 'ADMIN':
        return 'Administrador';
      case 'COORDENADOR':
        return 'Coordenador';
      case 'ALUNO':
        return 'Aluno';
      case 'ORIENTADOR':
        return 'Orientador';
      default:
        return 'Sessão';
    }
  }

  private buildLinks(perfil: UserPerfil | null): PainelNavLink[] {
    switch (perfil) {
      case 'ADMIN':
        return [
          { label: 'Painel do Admin', shortLabel: 'Admin', path: '/painel/admin', primary: true },
          { label: 'Logs do Sistema', shortLabel: 'Logs', path: '/painel/logs-sistema', primary: true },
          { label: 'Portal Público', shortLabel: 'Portal', path: '/consultor-externo', primary: true },
        ];
      case 'COORDENADOR':
        return [
          { label: 'Painel do Coordenador', shortLabel: 'Painel', path: '/painel/coordenador', primary: true },
          { label: 'Períodos Letivos', shortLabel: 'Períodos', path: '/painel/gerenciar-periodos', primary: true },
          { label: 'Definição de Prazos', shortLabel: 'Prazos', path: '/painel/criar-periodo', primary: true },
          { label: 'Visão Geral', shortLabel: 'Visão', path: '/painel/visao-geral', primary: true },
          { label: 'Histórico de Submissões', shortLabel: 'Histórico', path: '/painel/historico-submissoes' },
          { label: 'Submissões Atrasadas', shortLabel: 'Atrasadas', path: '/painel/submissoes-atrasadas' },
          { label: 'Portal Público', shortLabel: 'Portal', path: '/consultor-externo' },
        ];
      case 'ALUNO':
        return [
          { label: 'Painel do Aluno', shortLabel: 'Painel', path: '/painel/aluno', primary: true },
          { label: 'Definir TCC', shortLabel: 'TCC', path: '/painel/definir-tcc', primary: true },
          { label: 'Submeter Entregáveis', shortLabel: 'Entregáveis', path: '/painel/submeter-entregaveis', primary: true },
          { label: 'Prazos do Período', shortLabel: 'Prazos', path: '/painel/prazos-periodo', primary: true },
          { label: 'Versão Final', shortLabel: 'Final', path: '/painel/submeter-versao-final' },
          { label: 'Status do Depósito', shortLabel: 'Depósito', path: '/painel/status-deposito' },
          { label: 'Notificações', shortLabel: 'Notificações', path: '/painel/notificacoes' },
          { label: 'Privacidade', shortLabel: 'Privacidade', path: '/painel/privacidade' },
          { label: 'Portal Público', shortLabel: 'Portal', path: '/consultor-externo' },
        ];
      case 'ORIENTADOR':
        return [
          { label: 'Painel do Orientador', shortLabel: 'Painel', path: '/painel/orientador', primary: true },
          { label: 'Aceites Pendentes', shortLabel: 'Aceites', path: '/painel/aceite-orientacao', primary: true },
          { label: 'Registrar Sessão', shortLabel: 'Sessão', path: '/painel/registrar-sessao', primary: true },
          { label: 'Registrar Banca', shortLabel: 'Banca', path: '/painel/registrar-banca', primary: true },
          { label: 'Prazos do Período', shortLabel: 'Prazos', path: '/painel/prazos-periodo' },
          { label: 'Histórico de Submissões', shortLabel: 'Histórico', path: '/painel/historico-submissoes' },
          { label: 'Notificações', shortLabel: 'Notificações', path: '/painel/notificacoes' },
          { label: 'Portal Público', shortLabel: 'Portal', path: '/consultor-externo' },
        ];
      default:
        return [];
    }
  }
}
