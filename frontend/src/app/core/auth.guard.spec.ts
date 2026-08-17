import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';
import { Observable, firstValueFrom, of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { authGuard, roleGuard } from './auth.guard';
import { AuthService } from './auth.service';
import { User } from './models';

const USER: User = {
  id: 2, first_name: 'Sara', last_name: 'Manager', email: 'sara@example.com', role: 'MANAGER',
  customer_id: null, is_active: true, created_at: '2026-01-01T08:00:00', updated_at: '2026-01-01T08:00:00',
};

describe('functional route guards', () => {
  const authMock = { ensureSession: vi.fn() };

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideRouter([]), { provide: AuthService, useValue: authMock }] });
  });

  it('redirects an anonymous visitor to login with the return URL', async () => {
    authMock.ensureSession.mockReturnValue(of(null));
    const result = TestBed.runInInjectionContext(() => authGuard({} as ActivatedRouteSnapshot, { url: '/tickets' } as RouterStateSnapshot));
    const resolved = await firstValueFrom(result as Observable<boolean | UrlTree>);
    expect(TestBed.inject(Router).serializeUrl(resolved as UrlTree)).toBe('/login?returnUrl=%2Ftickets');
  });

  it('rejects a manager from an administrator-only route', async () => {
    authMock.ensureSession.mockReturnValue(of(USER));
    const route = { data: { roles: ['ADMIN'] } } as unknown as ActivatedRouteSnapshot;
    const result = TestBed.runInInjectionContext(() => roleGuard(route, {} as RouterStateSnapshot));
    const resolved = await firstValueFrom(result as Observable<boolean | UrlTree>);
    expect(TestBed.inject(Router).serializeUrl(resolved as UrlTree)).toBe('/dashboard');
  });
});
