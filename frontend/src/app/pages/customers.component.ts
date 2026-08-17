import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize } from 'rxjs';

import { apiErrorMessage } from '../core/api-error';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Customer } from '../core/models';

@Component({
  selector: 'app-customers',
  imports: [ReactiveFormsModule],
  template: `
    <header class="page-header"><div><p class="eyebrow">RÉFÉRENTIEL</p><h1>Clients</h1><p>Coordonnées des entreprises accompagnées.</p></div>@if (canManage()) { <button class="button button-primary" type="button" (click)="openCreate()">+ Ajouter un client</button> }</header>
    @if (error()) { <div class="alert alert-error">{{ error() }}</div> }
    @if (success()) { <div class="alert alert-success">{{ success() }}</div> }
    @if (showForm()) {
      <section class="panel form-card">
        <div class="panel-header"><div><h2>{{ editingId() ? 'Modifier le client' : 'Nouveau client' }}</h2><p>Les champs marqués d'un astérisque sont obligatoires.</p></div><button class="icon-button" type="button" (click)="closeForm()" aria-label="Fermer">×</button></div>
        <form class="form-grid two-columns" [formGroup]="form" (ngSubmit)="save()">
          <label>Raison sociale <span class="required">*</span><input formControlName="company_name" maxlength="200"></label>
          <label>Personne à contacter<input formControlName="contact_name" maxlength="200"></label>
          <label>E-mail<input type="email" formControlName="email"></label>
          <label>Téléphone<input type="tel" formControlName="phone" maxlength="50"></label>
          <label class="span-full">Adresse<textarea formControlName="address" rows="2" maxlength="500"></textarea></label>
          <div class="form-submit span-full"><button class="button button-ghost" type="button" (click)="closeForm()">Annuler</button><button class="button button-primary" type="submit" [disabled]="form.invalid || saving()">{{ saving() ? 'Enregistrement…' : 'Enregistrer' }}</button></div>
        </form>
      </section>
    }
    <section class="panel table-panel">
      <div class="panel-header"><div><h2>Répertoire</h2><p>{{ filteredCustomers().length }} client(s)</p></div><label class="search-field"><span class="sr-only">Rechercher</span><input [formControl]="search" placeholder="Rechercher un client…"></label></div>
      @if (loading()) { <div class="loading-card">Chargement des clients…</div> }
      @else if (filteredCustomers().length) {
        <div class="table-scroll"><table><thead><tr><th>Entreprise</th><th>Contact</th><th>E-mail</th><th>Téléphone</th><th>Statut</th>@if (canManage()) { <th>Actions</th> }</tr></thead><tbody>
          @for (customer of filteredCustomers(); track customer.id) {
            <tr><td><strong>{{ customer.company_name }}</strong><small>{{ customer.address || '—' }}</small></td><td>{{ customer.contact_name || '—' }}</td><td>{{ customer.email || '—' }}</td><td>{{ customer.phone || '—' }}</td><td><span class="badge" [class.status-closed]="!customer.is_active">{{ customer.is_active ? 'Actif' : 'Inactif' }}</span></td>@if (canManage()) { <td class="action-cell"><button class="link-button" type="button" (click)="openEdit(customer)">Modifier</button><button class="link-button" type="button" (click)="toggleActive(customer)">{{ customer.is_active ? 'Désactiver' : 'Réactiver' }}</button></td> }</tr>
          }
        </tbody></table></div>
      } @else { <div class="empty-state"><strong>Aucun client</strong><p>Aucun résultat ne correspond à la recherche.</p></div> }
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CustomersComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);
  readonly customers = signal<Customer[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal('');
  readonly success = signal('');
  readonly showForm = signal(false);
  readonly editingId = signal<number | null>(null);
  readonly canManage = computed(() => this.auth.hasAnyRole('ADMIN', 'MANAGER'));
  readonly search = this.fb.nonNullable.control('');
  filteredCustomers(): Customer[] {
    const query = this.search.value.trim().toLowerCase();
    return query ? this.customers().filter((item) => `${item.company_name} ${item.contact_name ?? ''} ${item.email ?? ''}`.toLowerCase().includes(query)) : this.customers();
  }
  readonly form = this.fb.nonNullable.group({
    company_name: ['', [Validators.required, Validators.maxLength(200)]],
    contact_name: ['', Validators.maxLength(200)], email: ['', Validators.email], phone: ['', Validators.maxLength(50)], address: ['', Validators.maxLength(500)],
  });

  ngOnInit(): void { this.load(); }
  load(): void {
    this.api.customers('', !this.canManage()).subscribe({ next: (items) => { this.customers.set(items); this.loading.set(false); }, error: (error: unknown) => { this.error.set(apiErrorMessage(error)); this.loading.set(false); } });
  }
  openCreate(): void { this.editingId.set(null); this.form.reset(); this.showForm.set(true); }
  openEdit(customer: Customer): void { this.editingId.set(customer.id); this.form.setValue({ company_name: customer.company_name, contact_name: customer.contact_name ?? '', email: customer.email ?? '', phone: customer.phone ?? '', address: customer.address ?? '' }); this.showForm.set(true); }
  closeForm(): void { this.showForm.set(false); this.editingId.set(null); this.form.reset(); }
  save(): void {
    if (this.form.invalid || !this.canManage()) return;
    const raw = this.form.getRawValue();
    const payload = { company_name: raw.company_name.trim(), contact_name: raw.contact_name.trim() || null, email: raw.email.trim() || null, phone: raw.phone.trim() || null, address: raw.address.trim() || null };
    const request = this.editingId() ? this.api.updateCustomer(this.editingId()!, payload) : this.api.createCustomer(payload);
    this.saving.set(true); this.error.set('');
    request.pipe(finalize(() => this.saving.set(false))).subscribe({ next: () => { this.success.set('Client enregistré.'); this.closeForm(); this.load(); }, error: (error: unknown) => this.error.set(apiErrorMessage(error)) });
  }
  toggleActive(customer: Customer): void {
    this.api.updateCustomer(customer.id, { is_active: !customer.is_active }).subscribe({ next: () => { this.success.set('Statut du client mis à jour.'); this.load(); }, error: (error: unknown) => this.error.set(apiErrorMessage(error)) });
  }
}
