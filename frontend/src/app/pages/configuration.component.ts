import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Observable, finalize, forkJoin } from 'rxjs';

import { apiErrorMessage } from '../core/api-error';
import { ApiService } from '../core/api.service';
import { Category, PRIORITIES, Priority, Product, ProductModule, SlaConfiguration, label } from '../core/models';

@Component({
  selector: 'app-configuration',
  imports: [ReactiveFormsModule],
  template: `
    <header class="page-header"><div><p class="eyebrow">ADMINISTRATION</p><h1>Catalogue & SLA</h1><p>Paramétrez la classification des tickets et les objectifs de traitement.</p></div></header>
    @if (error()) { <div class="alert alert-error">{{ error() }}</div> }
    @if (success()) { <div class="alert alert-success">{{ success() }}</div> }

    <section class="panel form-card">
      <div class="panel-header"><div><h2>Engagements de service</h2><p>Durée cible et seuil d'alerte par niveau de priorité.</p></div></div>
      <div class="sla-config-grid">
        @for (priority of priorities; track priority) {
          <article class="sla-config-item">
            <span class="priority" [class]="'priority-' + priority.toLowerCase()"><i></i>{{ displayLabel(priority) }}</span>
            <label>Objectif (heures)<input #target type="number" min="1" max="8760" [value]="slaFor(priority)?.target_hours ?? defaultHours(priority)"></label>
            <label>Seuil d'alerte (%)<input #warning type="number" min="1" max="100" [value]="slaFor(priority)?.warning_threshold_percent ?? 80"></label>
            <label class="checkbox-label"><input #active type="checkbox" [checked]="slaFor(priority)?.is_active ?? true"> Règle active</label>
            <button class="button button-secondary button-small" type="button" [disabled]="saving()" (click)="saveSla(priority, target.valueAsNumber, warning.valueAsNumber, active.checked)">Enregistrer</button>
          </article>
        }
      </div>
      <p class="form-note"><strong>Hypothèse — à valider avec Alias Informatique :</strong> les durées sont comptées en heures calendaires, sans calendrier ouvré.</p>
    </section>

    <div class="configuration-grid">
      <section class="panel form-card">
        <div class="panel-header"><div><h2>Produits</h2><p>{{ products().length }} élément(s)</p></div></div>
        <form class="inline-create" [formGroup]="productForm" (ngSubmit)="createProduct()"><input formControlName="name" placeholder="Nom du produit"><input formControlName="description" placeholder="Description (facultative)"><button class="button button-primary button-small" type="submit" [disabled]="productForm.invalid || saving()">Ajouter</button></form>
        <div class="simple-list">@for (product of products(); track product.id) { <div><span><strong>{{ product.name }}</strong><small>{{ product.description || 'Aucune description' }}</small></span><button class="link-button" type="button" (click)="toggleProduct(product)">{{ product.is_active ? 'Désactiver' : 'Réactiver' }}</button></div> } @empty { <p class="empty-state">Aucun produit.</p> }</div>
      </section>
      <section class="panel form-card">
        <div class="panel-header"><div><h2>Catégories</h2><p>{{ categories().length }} élément(s)</p></div></div>
        <form class="inline-create" [formGroup]="categoryForm" (ngSubmit)="createCategory()"><input formControlName="name" placeholder="Nom de la catégorie"><input formControlName="description" placeholder="Description (facultative)"><button class="button button-primary button-small" type="submit" [disabled]="categoryForm.invalid || saving()">Ajouter</button></form>
        <div class="simple-list">@for (category of categories(); track category.id) { <div><span><strong>{{ category.name }}</strong><small>{{ category.description || 'Aucune description' }}</small></span><button class="link-button" type="button" (click)="toggleCategory(category)">{{ category.is_active ? 'Désactiver' : 'Réactiver' }}</button></div> } @empty { <p class="empty-state">Aucune catégorie.</p> }</div>
      </section>
      <section class="panel form-card configuration-wide">
        <div class="panel-header"><div><h2>Modules</h2><p>Modules rattachés aux produits</p></div></div>
        <form class="inline-create modules-create" [formGroup]="moduleForm" (ngSubmit)="createModule()"><select formControlName="product_id"><option [ngValue]="0" disabled>Produit…</option>@for (product of activeProducts(); track product.id) { <option [ngValue]="product.id">{{ product.name }}</option> }</select><input formControlName="name" placeholder="Nom du module"><input formControlName="description" placeholder="Description (facultative)"><button class="button button-primary button-small" type="submit" [disabled]="moduleForm.invalid || saving()">Ajouter</button></form>
        <div class="simple-list module-list">@for (module of modules(); track module.id) { <div><span><strong>{{ module.name }}</strong><small>{{ productName(module.product_id) }} · {{ module.description || 'Aucune description' }}</small></span><button class="link-button" type="button" (click)="toggleModule(module)">{{ module.is_active ? 'Désactiver' : 'Réactiver' }}</button></div> } @empty { <p class="empty-state">Aucun module.</p> }</div>
      </section>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConfigurationComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);
  readonly priorities = PRIORITIES;
  readonly products = signal<Product[]>([]);
  readonly modules = signal<ProductModule[]>([]);
  readonly categories = signal<Category[]>([]);
  readonly sla = signal<SlaConfiguration[]>([]);
  readonly saving = signal(false);
  readonly error = signal('');
  readonly success = signal('');
  readonly productForm = this.fb.nonNullable.group({ name: ['', [Validators.required, Validators.maxLength(150)]], description: ['', Validators.maxLength(500)] });
  readonly categoryForm = this.fb.nonNullable.group({ name: ['', [Validators.required, Validators.maxLength(150)]], description: ['', Validators.maxLength(500)] });
  readonly moduleForm = this.fb.nonNullable.group({ product_id: [0, Validators.min(1)], name: ['', [Validators.required, Validators.maxLength(150)]], description: ['', Validators.maxLength(500)] });

  ngOnInit(): void { this.load(); }
  load(): void {
    forkJoin({ products: this.api.products(false), modules: this.api.modules(undefined, false), categories: this.api.categories(false), sla: this.api.slaConfigurations() }).subscribe({
      next: (data) => { this.products.set(data.products); this.modules.set(data.modules); this.categories.set(data.categories); this.sla.set(data.sla); },
      error: (error: unknown) => this.error.set(apiErrorMessage(error)),
    });
  }
  activeProducts(): Product[] { return this.products().filter((item) => item.is_active); }
  productName(id: number): string { return this.products().find((item) => item.id === id)?.name ?? `Produit #${id}`; }
  slaFor(priority: Priority): SlaConfiguration | undefined { return this.sla().find((item) => item.priority === priority); }
  defaultHours(priority: Priority): number { return ({ LOW: 72, MEDIUM: 24, HIGH: 8, CRITICAL: 4 })[priority]; }
  displayLabel(value: string): string { return label(value); }

  createProduct(): void { if (this.productForm.invalid) return; const value = this.productForm.getRawValue(); this.execute(this.api.createProduct({ name: value.name.trim(), description: value.description.trim() || null }), () => this.productForm.reset(), 'Produit ajouté.'); }
  createCategory(): void { if (this.categoryForm.invalid) return; const value = this.categoryForm.getRawValue(); this.execute(this.api.createCategory({ name: value.name.trim(), description: value.description.trim() || null }), () => this.categoryForm.reset(), 'Catégorie ajoutée.'); }
  createModule(): void { if (this.moduleForm.invalid) return; const value = this.moduleForm.getRawValue(); this.execute(this.api.createModule({ product_id: value.product_id, name: value.name.trim(), description: value.description.trim() || null }), () => this.moduleForm.reset(), 'Module ajouté.'); }
  toggleProduct(item: Product): void { this.execute(this.api.updateProduct(item.id, { is_active: !item.is_active }), () => undefined, 'Produit mis à jour.'); }
  toggleCategory(item: Category): void { this.execute(this.api.updateCategory(item.id, { is_active: !item.is_active }), () => undefined, 'Catégorie mise à jour.'); }
  toggleModule(item: ProductModule): void { this.execute(this.api.updateModule(item.id, { is_active: !item.is_active }), () => undefined, 'Module mis à jour.'); }
  saveSla(priority: Priority, targetHours: number, warningPercent: number, active: boolean): void {
    if (!Number.isFinite(targetHours) || targetHours < 1 || targetHours > 8760 || !Number.isFinite(warningPercent) || warningPercent < 1 || warningPercent > 100) { this.error.set('Les valeurs SLA ne sont pas valides.'); return; }
    this.execute(this.api.saveSla(priority, { target_hours: targetHours, warning_threshold_percent: warningPercent, is_active: active }), () => undefined, `SLA ${label(priority)} enregistré.`);
  }
  private execute(request: Observable<unknown>, reset: () => void, message: string): void {
    this.saving.set(true); this.error.set(''); this.success.set('');
    request.pipe(finalize(() => this.saving.set(false))).subscribe({ next: () => { reset(); this.success.set(message); this.load(); }, error: (error: unknown) => this.error.set(apiErrorMessage(error)) });
  }
}
