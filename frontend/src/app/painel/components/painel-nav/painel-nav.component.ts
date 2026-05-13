import { Component } from '@angular/core';

import { AuthService, UserPerfil } from '../../../auth/services/auth.service';

interface PainelNavLink {
  label: string;
  path: string;
}

@Component({
  selector: 'app-painel-nav',
  templateUrl: './painel-nav.component.html',
  styleUrls: ['./painel-nav.component.css'],
})
export class PainelNavComponent {
  readonly perfil = this.authService.getStoredPerfil();
  readonly links = this.buildLinks(this.perfil);
  readonly perfilLabel = this.getPerfilLabel(this.perfil);

  constructor(private readonly authService: AuthService) {}

  private getPerfilLabel(perfil: UserPerfil | null): string {
    switch (perfil) {
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
      case 'COORDENADOR':
        return [
          { label: 'Painel do Coordenador', path: '/painel/coordenador' },
          { label: 'Gerenciamento de Períodos Letivos', path: '/painel/gerenciar-periodos' },
          { label: 'Definição de Prazos do Período', path: '/painel/criar-periodo' },
        ];
      case 'ALUNO':
        return [
          { label: 'Painel do Aluno', path: '/painel/aluno' },
          { label: 'Definição de Tema, Tipo e Orientador', path: '/painel/definir-tcc' },
          { label: 'Prazos do Período', path: '/painel/prazos-periodo' },
        ];
      case 'ORIENTADOR':
        return [
          { label: 'Painel do Orientador', path: '/painel/orientador' },
          { label: 'Aceite do Orientador', path: '/painel/aceite-orientacao' },
          { label: 'Prazos do Período', path: '/painel/prazos-periodo' },
        ];
      default:
        return [];
    }
  }
}
