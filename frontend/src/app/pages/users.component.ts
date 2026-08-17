import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize } from 'rxjs';

import { apiErrorMessage } from '../core/api-error';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Customer, ROLES, Role, User, label } from '../core/models';

@Component({
  selector: 'app-users',
  imports: [ReactiveFormsModule],
  template: `
    <header class="page-header"><div><p class="eyebrow">ADMINISTRATION</p><h1>Utilisateurs</h1><p>Comptes, rôles et accès à l'application.</p></div><button class="button button-primary" type="button" (click)="openCreate()">+ Nouvel utilisateur</button></header>
    @if (error()) { <div class="alert alert-error">{{ error() }}</div> }
    @if (success()) { <div class="alert alert-success">{{ success() }}</div> }
    @if (showForm()) {
      <section class="panel form-card">
        <div class="panel-header"><div><h2>{{ editingId() ? 'Modifier le compte' : 'Créer un compte' }}</h2><p>Un client doit obligatoirement être lié à une entreprise.</p></div><button class="icon-button" type="button" (click)="closeForm()">×</button></div>
        <form class="form-grid two-columns" [formGroup]="form" (ngSubmit)="save()">
          <label>Prénom <span class="required">*</span><input formControlName="first_name" maxlength="100"></label>
          <label>Nom <span class="required">*</span><input formControlName="last_name" maxlength="100"></label>
          <label>E-mail <span class="required">*</span><input type="email" formControlName="email"></label>
          @if (!editingId()) { <label>Mot de passe initial <span class="required">*</span><input type="password" formControlName="password" minlength="8" autocomplete="new-password"><small>8 caractères minimum</small></label> }
          <label>Rôle <span class="required">*</span><select formControlName="role">@for (role of roles; track role) { <option [ngValue]="role">{{ displayLabel(role) }}</option> }</select></label>
          @if (form.controls.role.value === 'CLIENT') { <label>Entreprise cliente <span class="required">*</span><select formControlName="customer_id"><option [ngValue]="null" disabled>Choisir…</option>@for (customer of customers(); track customer.id) { <option [ngValue]="customer.id">{{ customer.company_name }}</option> }</select></label> }
          <label class="checkbox-label"><input type="checkbox" formControlName="is_active"> Compte actif</label>
          <div class="form-submit span-full"><button class="button button-ghost" type="button" (click)="closeForm()">Annuler</button><button class="button button-primary" type="submit" [disabled]="saving()">{{ saving() ? 'Enregistrement…' : 'Enregistrer' }}</button></div>
        </form>
      </section>
    }
    <section class="panel table-panel">
      <div class="panel-header"><div><h2>Comptes utilisateurs</h2><p>{{ users().length }} compte(s)</p></div></div>
      @if (loading()) { <div class="loading-card">Chargement des utilisateurs…</div> }
      @else { <div class="table-scroll"><table><thead><tr><th>Utilisateur</th><th>Rôle</th><th>Client associé</th><th>Statut</th><th>Création</th><th>Actions</th></tr></thead><tbody>
        @for (user of users(); track user.id) { <tr><td><div class="user-cell"><span class="avatar avatar-small">{{ initials(user) }}</span><span><strong>{{ user.first_name }} {{ user.last_name }}</strong><small>{{ user.email }}</small></span></div></td><td><span class="badge">{{ displayLabel(user.role) }}</span></td><td>{{ customerName(user.customer_id) }}</td><td><span class="badge" [class.status-closed]="!user.is_active">{{ user.is_active ? 'Actif' : 'Inactif' }}</span></td><td>{{ formatDate(user.created_at) }}</td><td class="action-cell"><button class="link-button" type="button" (click)="openEdit(user)">Modifier</button><button class="link-button" type="button" [disabled]="user.id === currentUserId()" (click)="toggleActive(user)">{{ user.is_active ? 'Désactiver' : 'Réactiver' }}</button></td></tr> }
      </tbody></table></div> }
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UsersComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  readonly roles = ROLES;
  readonly users = signal<User[]>([]);
  readonly customers = signal<Customer[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal('');
  readonly success = signal('');
  readonly showForm = signal(false);
  readonly editingId = signal<number | null>(null);
  readonly form = this.fb.group({
    first_name: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(100)]),
    last_name: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(100)]),
    email: this.fb.nonNullable.control('', [Validators.required, Validators.email]),
    password: this.fb.nonNullable.control(''), role: this.fb.nonNullable.control<Role>('AGENT'),
    customer_id: this.fb.control<number | null>(null), is_active: this.fb.nonNullable.control(true),
  });

  ngOnInit(): void {
    this.load();
    this.api.customers().subscribe({ next: (items) => this.customers.set(items) });
    this.form.controls.role.valueChanges.subscribe((role) => { if (role !== 'CLIENT') this.form.controls.customer_id.setValue(null); });
  }
  load(): void { this.api.users({ active_only: false }).subscribe({ next: (items) => { this.users.set(items); this.loading.set(false); }, error: (error: unknown) => { this.error.set(apiErrorMessage(error)); this.loading.set(false); } }); }
  openCreate(): void { this.editingId.set(null); this.form.reset(); this.form.controls.role.setValue('AGENT'); this.form.controls.is_active.setValue(true); this.showForm.set(true); }
  openEdit(user: User): void { this.editingId.set(user.id); this.form.setValue({ first_name: user.first_name, last_name: user.last_name, email: user.email, password: '', role: user.role, customer_id: user.customer_id, is_active: user.is_active }); this.showForm.set(true); }
  closeForm(): void { this.showForm.set(false); this.editingId.set(null); }
  save(): void {
    const value = this.form.getRawValue();
    if (this.form.invalid || (!this.editingId() && value.password.length < 8) || (value.role === 'CLIENT' && !value.customer_id)) { this.form.markAllAsTouched(); this.error.set('Vérifiez les champs obligatoires.'); return; }
    const common = { first_name: value.first_name.trim(), last_name: value.last_name.trim(), email: value.email.trim(), role: value.role, customer_id: value.role === 'CLIENT' ? value.customer_id : null, is_active: value.is_active };
    const request = this.editingId() ? this.api.updateUser(this.editingId()!, common) : this.api.createUser({ ...common, password: value.password });
    this.saving.set(true); this.error.set('');
    request.pipe(finalize(() => this.saving.set(false))).subscribe({ next: () => { this.success.set('Compte enregistré.'); this.closeForm(); this.load(); }, error: (error: unknown) => this.error.set(apiErrorMessage(error)) });
  }
  toggleActive(user: User): void { this.api.updateUser(user.id, { is_active: !user.is_active }).subscribe({ next: () => { this.success.set('Statut du compte mis à jour.'); this.load(); }, error: (error: unknown) => this.error.set(apiErrorMessage(error)) }); }
  displayLabel(value: string): string { return label(value); }
  customerName(id: number | null): string { return id ? (this.customers().find((customer) => customer.id === id)?.company_name ?? `Client #${id}`) : '—'; }
  initials(user: User): string { return `${user.first_name[0] ?? ''}${user.last_name[0] ?? ''}`.toUpperCase(); }
  formatDate(value: string): string { return new Intl.DateTimeFormat('fr-FR').format(new Date(value)); }
  currentUserId(): number { return this.auth.user()?.id ?? 0; }
}
