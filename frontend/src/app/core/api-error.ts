import { HttpErrorResponse } from '@angular/common/http';

export function apiErrorMessage(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    const detail: unknown = error.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((item: { msg?: string }) => item.msg ?? 'Valeur invalide').join(' ');
    }
    if (error.status === 0) return 'API indisponible. Vérifiez que le serveur FastAPI est démarré.';
  }
  return 'Une erreur inattendue est survenue.';
}
