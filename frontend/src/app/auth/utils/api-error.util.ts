import { HttpErrorResponse } from '@angular/common/http';

export function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
  if (!(error instanceof HttpErrorResponse)) {
    return fallbackMessage;
  }

  const detail = error.error?.detail;
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  const message = error.error?.mensagem;
  if (typeof message === 'string' && message.trim()) {
    return message;
  }

  return fallbackMessage;
}
