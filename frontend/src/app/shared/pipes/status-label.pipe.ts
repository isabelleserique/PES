import { Pipe, PipeTransform } from '@angular/core';

/**
 * Converte os valores crus de enum (vindos da API, em UPPER_SNAKE_CASE)
 * em rótulos legíveis para o usuário final.
 *
 * Ex.: 'EM_ANDAMENTO' -> 'Em andamento', 'A_VENCER' -> 'A vencer'.
 *
 * Valores não mapeados recebem um tratamento genérico (remove '_',
 * mantém apenas a primeira letra maiúscula) para nunca expor o '_'.
 */
@Pipe({ name: 'statusLabel' })
export class StatusLabelPipe implements PipeTransform {
  private static readonly labels: Record<string, string> = {
    // StatusTcc
    AGUARDANDO_ACEITE: 'Aguardando aceite',
    EM_ANDAMENTO: 'Em andamento',
    SEM_ORIENTADOR: 'Sem orientador',
    APROVADO: 'Aprovado',
    REJEITADO: 'Rejeitado',
    // StatusPrazo
    A_VENCER: 'A vencer',
    PROXIMO: 'Próximo',
    HOJE: 'Hoje',
    VENCIDO: 'Vencido',
    // StatusDeposito
    AGUARDANDO_ENVIO: 'Aguardando envio',
    EM_REVISAO: 'Em revisão',
    DEVOLVIDO_CORRECAO: 'Devolvido para correção',
    DEPOSITADO: 'Depositado',
    // Status de usuário / vínculo
    PENDENTE: 'Pendente',
    ATIVO: 'Ativo',
    ACEITO: 'Aceito',
    RECUSADO: 'Recusado',
  };

  transform(value: string | null | undefined): string {
    if (value === null || value === undefined || value === '') {
      return '';
    }

    const chave = value.trim().toUpperCase();
    if (StatusLabelPipe.labels[chave]) {
      return StatusLabelPipe.labels[chave];
    }

    // Fallback genérico: garante que nenhum '_' chegue ao usuário.
    const texto = chave.replace(/_/g, ' ').toLowerCase();
    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }
}
