import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { AuthService } from './auth.service';
import { User } from './models';

const USER: User = {
  id: 1,
  first_name: 'Admin',
  last_name: 'Alias',
  email: 'admin@example.com',
  role: 'ADMIN',
  customer_id: null,
  is_active: true,
  created_at: '2026-01-01T08:00:00',
  updated_at: '2026-01-01T08:00:00',
};

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('stores the bearer token and loads the authenticated profile', () => {
    let result: User | undefined;
    service.login('admin@example.com', 'Password123!').subscribe((user) => (result = user));

    const loginRequest = http.expectOne('/api/auth/login');
    expect(loginRequest.request.method).toBe('POST');
    expect(loginRequest.request.body).toEqual({ email: 'admin@example.com', password: 'Password123!' });
    loginRequest.flush({ access_token: 'signed-token', token_type: 'bearer' });

    const profileRequest = http.expectOne('/api/auth/me');
    expect(profileRequest.request.method).toBe('GET');
    profileRequest.flush(USER);

    expect(result).toEqual(USER);
    expect(service.user()).toEqual(USER);
    expect(service.token).toBe('signed-token');
  });

  it('clears local authentication state on logout', () => {
    localStorage.setItem('alias_support_token', 'token');
    service.logout();
    expect(service.token).toBeNull();
    expect(service.user()).toBeNull();
  });
});
