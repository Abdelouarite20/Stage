import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { apiErrorMessage } from '../core/api-error';
import { ApiService } from '../core/api.service';
import { Notification, label } from '../core/models';

@Component({
  selector: 'app-notifications',
  imports: [DatePipe, RouterLink],
  template: `
    <header class="page-header"><div><p class="eyebrow">CENTRE D'ALERTES</p><h1>Notifications</h1><p>Affectations, échéances et mises à jour importantes.</p></div><button class="button button-secondary" type="button" [disabled]="!hasUnread()" (click)="markAllRead()">Tout marquer comme lu</button></header>
    @if (error()) { <div class="alert alert-error">{{ error() }}</div> }
    <div class="notification-toolbar"><label class="checkbox-label"><input type="checkbox" [checked]="unreadOnly()" (change)="toggleUnread()"> Afficher uniquement les non lues</label></div>
    <section class="panel notification-panel">
      @if (loading()) { <div class="loading-card">Chargement des notifications…</div> }
      @else {
        <div class="notification-list">
          @for (notification of notifications(); track notification.id) {
            <article class="notification-item" [class.unread]="!notification.is_read">
              <span class="notification-icon" [class.notification-warning]="notification.type.includes('OVERDUE') || notification.type.includes('WARNING')">{{ icon(notification.type) }}</span>
              <div><div class="notification-title"><strong>{{ notification.title }}</strong>@if (!notification.is_read) { <i>Non lue</i> }</div><p>{{ notification.message }}</p><small>{{ displayLabel(notification.type) }} · {{ notification.created_at | date:'dd/MM/yyyy à HH:mm' }}</small></div>
              <div class="notification-actions">@if (notification.ticket_id) { <a class="button button-ghost button-small" [routerLink]="['/tickets', notification.ticket_id]" (click)="markRead(notification)">Voir le ticket</a> } @if (!notification.is_read) { <button class="link-button" type="button" (click)="markRead(notification)">Marquer comme lue</button> }</div>
            </article>
          } @empty { <div class="empty-state"><strong>Aucune notification</strong><p>Les nouvelles alertes apparaîtront ici.</p></div> }
        </div>
      }
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotificationsComponent implements OnInit {
  private readonly api = inject(ApiService);
  readonly notifications = signal<Notification[]>([]);
  readonly unreadOnly = signal(false);
  readonly loading = signal(true);
  readonly error = signal('');

  ngOnInit(): void { this.load(); }
  load(): void { this.loading.set(true); this.api.notifications(this.unreadOnly()).subscribe({ next: (items) => { this.notifications.set(items); this.loading.set(false); }, error: (error: unknown) => { this.error.set(apiErrorMessage(error)); this.loading.set(false); } }); }
  toggleUnread(): void { this.unreadOnly.update((value) => !value); this.load(); }
  hasUnread(): boolean { return this.notifications().some((item) => !item.is_read); }
  markRead(item: Notification): void { if (item.is_read) return; this.api.readNotification(item.id).subscribe({ next: () => this.load(), error: (error: unknown) => this.error.set(apiErrorMessage(error)) }); }
  markAllRead(): void { this.api.readAllNotifications().subscribe({ next: () => this.load(), error: (error: unknown) => this.error.set(apiErrorMessage(error)) }); }
  displayLabel(value: string): string { return label(value); }
  icon(type: string): string { return type === 'ASSIGNMENT' ? '→' : type.includes('SLA') ? '⏱' : type.includes('TASK') ? '✓' : '•'; }
}
