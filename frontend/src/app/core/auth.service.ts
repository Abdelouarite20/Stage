import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, catchError, finalize, map, of, shareReplay, switchMap, tap } from 'rxjs';

import { Role, TokenResponse, User } from './models';

const TOKEN_KEY = 'alias_support_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly currentUser = signal<User | null>(null);
  private profileRequest: Observable<User | null> | null = null;

  readonly user = this.currentUser.asReadonly();
  readonly isAuthenticated = computed(() => this.currentUser() !== null);
  readonly role = computed(() => this.currentUser()?.role ?? null);

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  login(email: string, password: string): Observable<User> {
    return this.http.post<TokenResponse>('/api/auth/login', { email, password }).pipe(
      tap(({ access_token }) => localStorage.setItem(TOKEN_KEY, access_token)),
      switchMap(() => this.http.get<User>('/api/auth/me')),
      tap((user) => this.currentUser.set(user)),
      catchError((error: unknown) => {
        this.clearSession();
        throw error;
      }),
    );
  }

  ensureSession(): Observable<User | null> {
    const user = this.currentUser();
    if (user) return of(user);
    if (!this.token) return of(null);
    if (!this.profileRequest) {
      this.profileRequest = this.http.get<User>('/api/auth/me').pipe(
        tap((profile) => this.currentUser.set(profile)),
        map((profile) => profile as User | null),
        catchError(() => {
          this.clearSession();
          return of(null);
        }),
        finalize(() => (this.profileRequest = null)),
        shareReplay(1),
      );
    }
    return this.profileRequest;
  }

  hasAnyRole(...roles: readonly Role[]): boolean {
    const currentRole = this.currentUser()?.role;
    return currentRole !== undefined && roles.includes(currentRole);
  }

  logout(): void {
    this.clearSession();
  }

  clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.currentUser.set(null);
    this.profileRequest = null;
  }
}
