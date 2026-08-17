import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { label } from '../core/models';

@Component({
  selector: 'app-shell',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  template: `
    <div class="app-shell">
      <aside class="sidebar" [class.sidebar-open]="menuOpen()">
        <a class="brand" routerLink="/dashboard" (click)="closeMenu()" aria-label="Accueil Alias Informatique">
          <img class="sidebar-logo" src="/images/alias-informatique-logo.png" alt="Alias Informatique">
        </a>
        <nav aria-label="Navigation principale">
          <a routerLink="/dashboard" routerLinkActive="active" (click)="closeMenu()"><span aria-hidden="true">▦</span> Tableau de bord</a>
          <a routerLink="/tickets" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }" (click)="closeMenu()"><span aria-hidden="true">▤</span> Tickets</a>
          <a routerLink="/tickets/new" routerLinkActive="active" (click)="closeMenu()"><span aria-hidden="true">+</span> Nouvelle demande</a>
          <a routerLink="/customers" routerLinkActive="active" (click)="closeMenu()"><span aria-hidden="true">◇</span> Clients</a>
          @if (auth.hasAnyRole('ADMIN')) {
            <p class="nav-section">Administration</p>
            <a routerLink="/users" routerLinkActive="active" (click)="closeMenu()"><span aria-hidden="true">◎</span> Utilisateurs</a>
            <a routerLink="/configuration" routerLinkActive="active" (click)="closeMenu()"><span aria-hidden="true">⚙</span> Catalogue & SLA</a>
          }
        </nav>
        <div class="sidebar-user">
          <span class="avatar">{{ initials() }}</span>
          <span><strong>{{ auth.user()?.first_name }} {{ auth.user()?.last_name }}</strong><small>{{ roleLabel() }}</small></span>
        </div>
      </aside>

      <div class="app-main">
        <header class="topbar">
          <button class="icon-button menu-button" type="button" (click)="menuOpen.set(!menuOpen())" aria-label="Ouvrir le menu">☰</button>
          <span class="topbar-spacer"></span>
          <a class="notification-link" routerLink="/notifications" aria-label="Notifications">
            <span aria-hidden="true">○</span>
            @if (unreadCount() > 0) { <span class="notification-count">{{ unreadCount() }}</span> }
          </a>
          <button class="button button-ghost button-small" type="button" (click)="logout()">Déconnexion</button>
        </header>
        <main class="page-container"><router-outlet /></main>
      </div>
      @if (menuOpen()) { <button class="menu-backdrop" type="button" aria-label="Fermer le menu" (click)="closeMenu()"></button> }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShellComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  readonly menuOpen = signal(false);
  readonly unreadCount = signal(0);

  ngOnInit(): void {
    this.api.unreadCount().subscribe({ next: ({ count }) => this.unreadCount.set(count) });
  }

  initials(): string {
    const user = this.auth.user();
    return user ? `${user.first_name[0] ?? ''}${user.last_name[0] ?? ''}`.toUpperCase() : '';
  }

  roleLabel(): string { return label(this.auth.user()?.role); }
  closeMenu(): void { this.menuOpen.set(false); }

  logout(): void {
    this.auth.logout();
    void this.router.navigate(['/login']);
  }
}
