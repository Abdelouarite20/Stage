import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found',
  imports: [RouterLink],
  template: `<section class="empty-page"><strong>404</strong><h1>Page introuvable</h1><p class="muted">L'adresse demandée n'existe pas.</p><a class="button button-primary" routerLink="/dashboard">Retour au tableau de bord</a></section>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotFoundComponent {}
