import { NgTemplateOutlet } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { apiErrorMessage } from '../core/api-error';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { DashboardCount, DashboardSummary, label } from '../core/models';

@Component({
  selector: 'app-dashboard',
  imports: [NgTemplateOutlet, RouterLink],
  template: `
    <header class="page-header">
      <div><p class="eyebrow">VUE D'ENSEMBLE</p><h1>Bonjour, {{ auth.user()?.first_name }}</h1><p>Voici la situation actuelle des demandes visibles par votre compte.</p></div>
      <a class="button button-primary" routerLink="/tickets/new">+ Nouvelle demande</a>
    </header>
    @if (error()) { <div class="alert alert-error">{{ error() }}</div> }
    @if (loading()) {
      <div class="loading-card">Chargement des indicateurs…</div>
    } @else if (summary(); as data) {
      <section class="kpi-grid" aria-label="Indicateurs clés">
        <article class="kpi-card"><span>Total</span><strong>{{ data.total_tickets }}</strong><small>tickets visibles</small></article>
        <article class="kpi-card"><span>Ouverts</span><strong>{{ data.open_tickets }}</strong><small>à suivre</small></article>
        <article class="kpi-card kpi-blue"><span>En cours</span><strong>{{ data.in_progress_tickets }}</strong><small>en traitement</small></article>
        <article class="kpi-card kpi-danger"><span>En retard</span><strong>{{ data.overdue_tickets }}</strong><small>SLA dépassé</small></article>
        <article class="kpi-card"><span>Conformité SLA</span><strong>{{ data.sla_compliance_rate === null ? '—' : data.sla_compliance_rate + '%' }}</strong><small>tickets résolus mesurables</small></article>
        <article class="kpi-card"><span>Résolution moyenne</span><strong>{{ data.average_resolution_hours === null ? '—' : data.average_resolution_hours + ' h' }}</strong><small>temps moyen</small></article>
      </section>
      <section class="dashboard-grid">
        <article class="panel">
          <div class="panel-header"><div><h2>Tickets par statut</h2><p>Répartition du portefeuille actuel</p></div></div>
          <div class="distribution-list">
            @for (item of data.by_status; track item.label) { <ng-container [ngTemplateOutlet]="bar" [ngTemplateOutletContext]="{ item: item, total: max(data.by_status) }" /> }
          </div>
        </article>
        <article class="panel">
          <div class="panel-header"><div><h2>Tickets par priorité</h2><p>Concentration des demandes urgentes</p></div></div>
          <div class="distribution-list">
            @for (item of data.by_priority; track item.label) { <ng-container [ngTemplateOutlet]="bar" [ngTemplateOutletContext]="{ item: item, total: max(data.by_priority) }" /> }
          </div>
        </article>
        <article class="panel">
          <div class="panel-header"><div><h2>Catégories principales</h2><p>Nature des demandes</p></div></div>
          <div class="distribution-list">
            @for (item of data.by_category; track item.label) { <ng-container [ngTemplateOutlet]="plainBar" [ngTemplateOutletContext]="{ item: item, total: max(data.by_category) }" /> }
            @empty { <p class="empty-state">Aucune donnée disponible.</p> }
          </div>
        </article>
        @if (auth.hasAnyRole('ADMIN', 'MANAGER')) {
          <article class="panel">
            <div class="panel-header"><div><h2>Tickets par client</h2><p>Entreprises générant le plus de demandes</p></div></div>
            <div class="distribution-list">
              @for (item of data.by_customer; track item.label) { <ng-container [ngTemplateOutlet]="plainBar" [ngTemplateOutletContext]="{ item: item, total: max(data.by_customer) }" /> }
              @empty { <p class="empty-state">Aucune donnée client.</p> }
            </div>
          </article>
          <article class="panel">
            <div class="panel-header"><div><h2>Charge par intervenant</h2><p>Répartition des tickets</p></div></div>
            <div class="distribution-list">
              @for (item of data.by_assignee; track item.label) { <ng-container [ngTemplateOutlet]="plainBar" [ngTemplateOutletContext]="{ item: item, total: max(data.by_assignee) }" /> }
              @empty { <p class="empty-state">Aucune affectation.</p> }
            </div>
          </article>
        }
      </section>
    }

    <ng-template #bar let-item="item" let-total="total">
      <div class="distribution-row"><div><span>{{ displayLabel(item.label) }}</span><strong>{{ item.count }}</strong></div><div class="bar-track"><span [style.width.%]="percent(item.count, total)"></span></div></div>
    </ng-template>
    <ng-template #plainBar let-item="item" let-total="total">
      <div class="distribution-row"><div><span>{{ item.label }}</span><strong>{{ item.count }}</strong></div><div class="bar-track"><span [style.width.%]="percent(item.count, total)"></span></div></div>
    </ng-template>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);
  readonly summary = signal<DashboardSummary | null>(null);
  readonly loading = signal(true);
  readonly error = signal('');
  readonly resolvedTotal = computed(() => (this.summary()?.resolved_tickets ?? 0) + (this.summary()?.closed_tickets ?? 0));

  ngOnInit(): void {
    this.api.dashboard().subscribe({
      next: (data) => { this.summary.set(data); this.loading.set(false); },
      error: (error: unknown) => { this.error.set(apiErrorMessage(error)); this.loading.set(false); },
    });
  }

  displayLabel(value: string): string { return label(value); }
  max(items: DashboardCount[]): number { return Math.max(1, ...items.map((item) => item.count)); }
  percent(value: number, maximum: number): number { return Math.max(4, value * 100 / maximum); }
}
