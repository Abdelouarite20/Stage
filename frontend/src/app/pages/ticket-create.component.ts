import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { apiErrorMessage } from '../core/api-error';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Category, Customer, PRIORITIES, Priority, Product, ProductModule, label } from '../core/models';

@Component({
  selector: 'app-ticket-create',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <header class="page-header compact-header">
      <div><a class="back-link" routerLink="/tickets">← Retour aux tickets</a><h1>Nouvelle demande</h1><p>Décrivez le besoin avec suffisamment de précision pour faciliter sa prise en charge.</p></div>
    </header>
    <form class="form-layout" [formGroup]="form" (ngSubmit)="submit()">
      <section class="panel form-card">
        <div class="panel-header"><div><span class="step-number">1</span><h2>Demandeur et classification</h2></div></div>
        @if (error()) { <div class="alert alert-error">{{ error() }}</div> }
        <div class="form-grid two-columns">
          <label>Client <span class="required">*</span>
            <select formControlName="customer_id"><option [ngValue]="0" disabled>Sélectionner un client</option>@for (customer of customers(); track customer.id) { <option [ngValue]="customer.id">{{ customer.company_name }}</option> }</select>
            @if (form.controls.customer_id.touched && form.controls.customer_id.invalid) { <small class="field-error">Le client est obligatoire.</small> }
          </label>
          <label>Catégorie <span class="required">*</span>
            <select formControlName="category_id"><option [ngValue]="0" disabled>Sélectionner une catégorie</option>@for (category of categories(); track category.id) { <option [ngValue]="category.id">{{ category.name }}</option> }</select>
          </label>
          <label>Produit
            <select formControlName="product_id"><option [ngValue]="null">Aucun / Non précisé</option>@for (product of products(); track product.id) { <option [ngValue]="product.id">{{ product.name }}</option> }</select>
          </label>
          <label>Module
            <select formControlName="module_id"><option [ngValue]="null">Aucun / Non précisé</option>@for (module of visibleModules(); track module.id) { <option [ngValue]="module.id">{{ module.name }}</option> }</select>
          </label>
          <label>Priorité <span class="required">*</span>
            <select formControlName="priority">@for (priority of priorities; track priority) { <option [ngValue]="priority">{{ displayLabel(priority) }}</option> }</select>
            @if (auth.hasAnyRole('CLIENT')) { <small>Les demandes client démarrent avec une priorité moyenne.</small> }
          </label>
        </div>
      </section>
      <section class="panel form-card">
        <div class="panel-header"><div><span class="step-number">2</span><h2>Description du problème</h2></div></div>
        <div class="form-stack">
          <label>Objet <span class="required">*</span><input formControlName="subject" maxlength="250" placeholder="Ex. Impossible d'exporter le journal comptable"><small>{{ form.controls.subject.value.length }}/250 caractères</small></label>
          <label>Description détaillée <span class="required">*</span><textarea formControlName="description" rows="8" maxlength="10000" placeholder="Contexte, comportement observé, message d'erreur et résultat attendu…"></textarea><small>{{ form.controls.description.value.length }}/10 000 caractères</small></label>
        </div>
      </section>
      <footer class="form-actions"><a class="button button-ghost" routerLink="/tickets">Annuler</a><button class="button button-primary" type="submit" [disabled]="submitting()">{{ submitting() ? 'Création…' : 'Créer le ticket' }}</button></footer>
    </form>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketCreateComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  readonly priorities = PRIORITIES;
  readonly customers = signal<Customer[]>([]);
  readonly categories = signal<Category[]>([]);
  readonly products = signal<Product[]>([]);
  readonly modules = signal<ProductModule[]>([]);
  readonly submitting = signal(false);
  readonly error = signal('');
  readonly form = this.fb.group({
    customer_id: this.fb.nonNullable.control(0, Validators.min(1)),
    category_id: this.fb.nonNullable.control(0, Validators.min(1)),
    product_id: this.fb.control<number | null>(null),
    module_id: this.fb.control<number | null>(null),
    priority: this.fb.nonNullable.control<Priority>('MEDIUM', Validators.required),
    subject: this.fb.nonNullable.control('', [Validators.required, Validators.minLength(3), Validators.maxLength(250)]),
    description: this.fb.nonNullable.control('', [Validators.required, Validators.minLength(3), Validators.maxLength(10000)]),
  });
  visibleModules(): ProductModule[] {
    const productId = this.form.controls.product_id.value;
    return productId ? this.modules().filter((module) => module.product_id === productId) : [];
  }

  ngOnInit(): void {
    this.api.customers().subscribe({ next: (items) => this.customers.set(items) });
    this.api.categories().subscribe({ next: (items) => this.categories.set(items) });
    this.api.products().subscribe({ next: (items) => this.products.set(items) });
    this.api.modules().subscribe({ next: (items) => this.modules.set(items) });
    this.form.controls.product_id.valueChanges.subscribe(() => this.form.controls.module_id.setValue(null));
    if (this.auth.hasAnyRole('CLIENT')) {
      this.form.controls.customer_id.setValue(this.auth.user()?.customer_id ?? 0);
      this.form.controls.customer_id.disable();
      this.form.controls.priority.setValue('MEDIUM');
      this.form.controls.priority.disable();
    }
  }

  submit(): void {
    if (this.form.invalid || this.submitting()) { this.form.markAllAsTouched(); return; }
    const value = this.form.getRawValue();
    this.submitting.set(true);
    this.error.set('');
    this.api.createTicket({
      customer_id: value.customer_id,
      category_id: value.category_id,
      module_id: value.module_id,
      priority: value.priority,
      subject: value.subject.trim(),
      description: value.description.trim(),
    }).pipe(finalize(() => this.submitting.set(false))).subscribe({
      next: (ticket) => void this.router.navigate(['/tickets', ticket.id]),
      error: (error: unknown) => this.error.set(apiErrorMessage(error)),
    });
  }

  displayLabel(value: string): string { return label(value); }
}
