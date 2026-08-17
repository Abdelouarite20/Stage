import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { debounceTime, distinctUntilChanged } from 'rxjs';

import { apiErrorMessage } from '../core/api-error';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Category, Customer, PRIORITIES, Product, ProductModule, TICKET_STATUSES, TicketFilters, TicketPage, User, label } from '../core/models';

@Component({
  selector: 'app-ticket-list',
  imports: [DatePipe, ReactiveFormsModule, RouterLink],
  template: `
    <header class="page-header">
      <div><p class="eyebrow">GESTION DES DEMANDES</p><h1>Tickets</h1><p>Recherchez, filtrez et suivez les demandes de support.</p></div>
      <a class="button button-primary" routerLink="/tickets/new">+ Nouvelle demande</a>
    </header>

    <form class="filter-panel" [formGroup]="filters" (ngSubmit)="applyFilters()">
      <label class="search-field"><span class="sr-only">Rechercher</span><input formControlName="search" placeholder="Référence ou objet…"></label>
      <label><span>Statut</span><select formControlName="status"><option value="">Tous</option>@for (status of statuses; track status) { <option [value]="status">{{ displayLabel(status) }}</option> }</select></label>
      <label><span>Priorité</span><select formControlName="priority"><option value="">Toutes</option>@for (priority of priorities; track priority) { <option [value]="priority">{{ displayLabel(priority) }}</option> }</select></label>
      <label><span>Catégorie</span><select formControlName="category_id"><option value="">Toutes</option>@for (category of categories(); track category.id) { <option [value]="category.id">{{ category.name }}</option> }</select></label>
      @if (!auth.hasAnyRole('CLIENT')) {
        <label><span>Client</span><select formControlName="customer_id"><option value="">Tous</option>@for (customer of customers(); track customer.id) { <option [value]="customer.id">{{ customer.company_name }}</option> }</select></label>
      }
      <label><span>Produit</span><select formControlName="product_id"><option value="">Tous</option>@for (product of products(); track product.id) { <option [value]="product.id">{{ product.name }}</option> }</select></label>
      <label><span>Module</span><select formControlName="module_id"><option value="">Tous</option>@for (module of visibleModules(); track module.id) { <option [value]="module.id">{{ module.name }}</option> }</select></label>
      @if (auth.hasAnyRole('ADMIN', 'MANAGER')) {
        <label><span>Intervenant</span><select formControlName="assigned_user_id"><option value="">Tous</option>@for (user of staff(); track user.id) { <option [value]="user.id">{{ user.first_name }} {{ user.last_name }}</option> }</select></label>
      }
      <label><span>SLA</span><select formControlName="sla_status"><option value="">Tous</option><option value="ON_TRACK">Dans les temps</option><option value="OVERDUE">En retard</option><option value="MET">Respecté (résolu)</option><option value="BREACHED">Dépassé (résolu)</option><option value="NOT_CONFIGURED">Non configuré</option></select></label>
      <label><span>Tri</span><select formControlName="sort_by"><option value="created_at">Date de création</option><option value="updated_at">Dernière mise à jour</option><option value="sla_deadline">Échéance SLA</option><option value="priority">Priorité</option><option value="reference">Référence</option></select></label>
      <button class="button button-secondary button-small" type="button" (click)="resetFilters()">Réinitialiser</button>
    </form>

    @if (error()) { <div class="alert alert-error">{{ error() }}</div> }
    <section class="panel table-panel">
      <div class="panel-header"><div><h2>{{ page()?.total ?? 0 }} ticket(s)</h2><p>Résultats correspondant aux filtres</p></div></div>
      @if (loading()) {
        <div class="loading-card">Chargement des tickets…</div>
      } @else if (page()?.items?.length) {
        <div class="table-scroll">
          <table>
            <thead><tr><th>Référence</th><th>Objet</th><th>Client</th><th>Statut</th><th>Priorité</th><th>Intervenant</th><th>SLA</th><th>Créé le</th><th></th></tr></thead>
            <tbody>
              @for (ticket of page()!.items; track ticket.id) {
                <tr>
                  <td><a class="reference-link" [routerLink]="['/tickets', ticket.id]">{{ ticket.reference }}</a></td>
                  <td><strong>{{ ticket.subject }}</strong><small>{{ categoryName(ticket.category_id) }}</small></td>
                  <td>{{ customerName(ticket.customer_id) }}</td>
                  <td><span class="badge" [class]="'badge status-' + ticket.status.toLowerCase()">{{ displayLabel(ticket.status) }}</span></td>
                  <td><span class="priority" [class]="'priority-' + ticket.priority.toLowerCase()"><i></i>{{ displayLabel(ticket.priority) }}</span></td>
                  <td>{{ ticket.assigned_user_name || userName(ticket.assigned_user_id) }}</td>
                  <td><span class="sla" [class.sla-overdue]="ticket.sla_status === 'OVERDUE' || ticket.sla_status === 'BREACHED'">{{ slaText(ticket.sla_status, ticket.sla_remaining_minutes) }}</span></td>
                  <td>{{ ticket.created_at | date:'dd/MM/yyyy' }}</td>
                  <td><a class="row-action" [routerLink]="['/tickets', ticket.id]" aria-label="Ouvrir le ticket">→</a></td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        <footer class="pagination">
          <span>Page {{ page()!.page }} sur {{ totalPages() }}</span>
          <div><button class="button button-ghost button-small" type="button" [disabled]="page()!.page <= 1" (click)="goToPage(page()!.page - 1)">← Précédent</button><button class="button button-ghost button-small" type="button" [disabled]="page()!.page >= totalPages()" (click)="goToPage(page()!.page + 1)">Suivant →</button></div>
        </footer>
      } @else {
        <div class="empty-state"><strong>Aucun ticket trouvé</strong><p>Modifiez les filtres ou créez une nouvelle demande.</p></div>
      }
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketListComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  readonly statuses = TICKET_STATUSES;
  readonly priorities = PRIORITIES;
  readonly page = signal<TicketPage | null>(null);
  readonly customers = signal<Customer[]>([]);
  readonly categories = signal<Category[]>([]);
  readonly products = signal<Product[]>([]);
  readonly modules = signal<ProductModule[]>([]);
  readonly staff = signal<User[]>([]);
  readonly loading = signal(true);
  readonly error = signal('');
  readonly currentPage = signal(1);
  readonly totalPages = computed(() => Math.max(1, Math.ceil((this.page()?.total ?? 0) / (this.page()?.page_size ?? 20))));
  visibleModules(): ProductModule[] {
    const productId = Number(this.filters.controls.product_id.value);
    return productId ? this.modules().filter((item) => item.product_id === productId) : this.modules();
  }
  readonly filters = this.fb.nonNullable.group({
    search: '', status: '', priority: '', category_id: '', customer_id: '', product_id: '', module_id: '', assigned_user_id: '', sla_status: '', sort_by: 'created_at',
  });

  ngOnInit(): void {
    this.loadLookups();
    this.loadTickets();
    this.filters.valueChanges.pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.currentPage.set(1);
      this.loadTickets();
    });
    this.filters.controls.product_id.valueChanges.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => this.filters.controls.module_id.setValue('', { emitEvent: false }));
  }

  loadLookups(): void {
    this.api.customers().subscribe({ next: (items) => this.customers.set(items) });
    this.api.categories().subscribe({ next: (items) => this.categories.set(items) });
    this.api.products().subscribe({ next: (items) => this.products.set(items) });
    this.api.modules().subscribe({ next: (items) => this.modules.set(items) });
    if (this.auth.hasAnyRole('ADMIN', 'MANAGER')) this.api.users().subscribe({ next: (items) => this.staff.set(items.filter((user) => user.role === 'AGENT' || user.role === 'MANAGER')) });
  }

  applyFilters(): void { this.currentPage.set(1); this.loadTickets(); }
  resetFilters(): void { this.filters.reset(); }
  goToPage(page: number): void { this.currentPage.set(page); this.loadTickets(); }

  loadTickets(): void {
    const value = this.filters.getRawValue();
    const numeric = (input: string): number | undefined => input ? Number(input) : undefined;
    const filters: TicketFilters = {
      search: value.search.trim() || undefined,
      status: value.status ? value.status as TicketFilters['status'] : undefined,
      priority: value.priority ? value.priority as TicketFilters['priority'] : undefined,
      category_id: numeric(value.category_id), customer_id: numeric(value.customer_id), product_id: numeric(value.product_id), module_id: numeric(value.module_id), assigned_user_id: numeric(value.assigned_user_id),
      sla_status: value.sla_status ? value.sla_status as TicketFilters['sla_status'] : undefined,
      sort_by: value.sort_by as NonNullable<TicketFilters['sort_by']>, sort_direction: 'desc', page: this.currentPage(), page_size: 20,
    };
    this.loading.set(true);
    this.error.set('');
    this.api.tickets(filters).subscribe({
      next: (result) => { this.page.set(result); this.loading.set(false); },
      error: (error: unknown) => { this.error.set(apiErrorMessage(error)); this.loading.set(false); },
    });
  }

  displayLabel(value: string): string { return label(value); }
  customerName(id: number): string { return this.customers().find((item) => item.id === id)?.company_name ?? `Client #${id}`; }
  categoryName(id: number): string { return this.categories().find((item) => item.id === id)?.name ?? `Catégorie #${id}`; }
  userName(id: number | null): string { const user = this.staff().find((item) => item.id === id); return user ? `${user.first_name} ${user.last_name}` : id ? `Utilisateur #${id}` : 'Non affecté'; }
  slaText(status: string, minutes: number | null): string {
    if (status === 'NOT_CONFIGURED') return 'Non configuré';
    if (minutes === null) return label(status);
    const absolute = Math.abs(minutes);
    const value = absolute >= 1440 ? `${Math.floor(absolute / 1440)} j` : absolute >= 60 ? `${Math.floor(absolute / 60)} h` : `${absolute} min`;
    return status === 'OVERDUE' ? `Retard ${value}` : `Reste ${value}`;
  }
}
