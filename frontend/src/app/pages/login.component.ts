import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { finalize } from 'rxjs';

import { apiErrorMessage } from '../core/api-error';
import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule],
  template: `
    <main class="login-page">
      <section class="login-intro">
        <div class="login-brand">
          <img class="login-logo" src="/images/alias-informatique-logo.png" alt="Alias Informatique">
        </div>
        <div>
          <p class="eyebrow">ESPACE SUPPORT</p>
          <h1>Centraliser. Prioriser.<br>Résoudre.</h1>
          <p>Une vue claire des demandes clients, des interventions et des engagements de service.</p>
        </div>
        <small>Application de gestion et de suivi des tickets</small>
      </section>
      <section class="login-panel">
        <form class="login-card" [formGroup]="form" (ngSubmit)="submit()">
          <img class="login-panel-logo" src="/images/alias-informatique-logo.png" alt="Alias Informatique">
          <div>
            <p class="eyebrow">BIENVENUE</p>
            <h2>Connexion</h2>
            <p class="muted">Saisissez vos identifiants pour accéder à votre espace.</p>
          </div>
          @if (error()) { <div class="alert alert-error" role="alert">{{ error() }}</div> }
          <label>Adresse e-mail
            <input type="email" formControlName="email" autocomplete="username" placeholder="nom@entreprise.ma">
          </label>
          <label>Mot de passe
            <input type="password" formControlName="password" autocomplete="current-password" placeholder="Votre mot de passe">
          </label>
          <button class="button button-primary button-block" type="submit" [disabled]="form.invalid || loading()">
            {{ loading() ? 'Connexion…' : 'Se connecter' }}
          </button>
        </form>
      </section>
    </main>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  submit(): void {
    this.form.controls.email.setValue(this.form.controls.email.value.trim());
    if (this.form.invalid || this.loading()) return;
    this.loading.set(true);
    this.error.set('');
    const { email, password } = this.form.getRawValue();
    this.auth.login(email, password).pipe(finalize(() => this.loading.set(false))).subscribe({
      next: () => void this.router.navigateByUrl(this.route.snapshot.queryParamMap.get('returnUrl') || '/dashboard'),
      error: (error: unknown) => this.error.set(apiErrorMessage(error)),
    });
  }
}
