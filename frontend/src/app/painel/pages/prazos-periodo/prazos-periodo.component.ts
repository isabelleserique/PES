import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';

export interface PrazoDisplay {
  nomeEtapa: string;
  dataLimite: Date;
  tipoDeTCC: string;
}

@Component({
  selector: 'app-prazos-periodo',
  templateUrl: './prazos-periodo.component.html',
  styleUrls: ['./prazos-periodo.component.css'],
})
export class PrazosPeriodoComponent {
  readonly filtroTipo = new FormControl<string>('Todos');
  readonly tiposDeTCC = ['Todos', 'Monografia', 'Artigo'];

  nomePeriodo = '';
  statusUsuario = '';
  isLoading = false;

  private _prazos: PrazoDisplay[] = [];

  get prazos(): PrazoDisplay[] {
    const filtro = this.filtroTipo.value;
    if (!filtro || filtro === 'Todos') return this._prazos;
    return this._prazos.filter((p) => p.tipoDeTCC === filtro || p.tipoDeTCC === 'Todos');
  }

  get prazosPendentes(): PrazoDisplay[] {
    return this.prazos;
  }

  getDiasRestantes(data: Date): number {
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    const d = new Date(data);
    d.setHours(0, 0, 0, 0);
    return Math.ceil((d.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24));
  }

  getDiasLabel(prazo: PrazoDisplay): string {
    const dias = this.getDiasRestantes(prazo.dataLimite);
    if (dias < 0) return `${Math.abs(dias)} dia(s) de atraso`;
    if (dias === 0) return 'Hoje';
    return `${dias} dia(s) restante(s)`;
  }

  getStatusClass(prazo: PrazoDisplay): string {
    const dias = this.getDiasRestantes(prazo.dataLimite);
    if (dias < 0) return 'status-atrasado';
    if (dias <= 7) return 'status-urgente';
    return 'status-ok';
  }

  getTipoEntrega(nomeEtapa: string): string {
    if (nomeEtapa.toLowerCase().includes('defesa')) return 'Defesa';
    return 'Entrega';
  }
}
