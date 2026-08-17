import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AuthService } from '../core/auth.service';
import { User } from '../core/models';
import { LoginComponent } from './login.component';

const USER: User = {
  id: 1, first_name: 'Admin', last_name: 'Alias', email: 'admin@example.com', role: 'ADMIN', customer_id: null,
  is_active: true, created_at: '2026-01-01T08:00:00', updated_at: '2026-01-01T08:00:00',
};

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  const authMock = { login: vi.fn() };

  beforeEach(async () => {
    authMock.login.mockReturnValue(of(USER));
    await TestBed.configureTestingModule({ imports: [LoginComponent], providers: [provideRouter([]), { provide: AuthService, useValue: authMock }] }).compileComponents();
    fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
  });

  it('keeps submission disabled while credentials are invalid', () => {
    const button = fixture.nativeElement.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('submits normalized valid credentials through AuthService', () => {
    fixture.componentInstance.form.setValue({ email: ' admin@example.com ', password: 'Password123!' });
    fixture.componentInstance.submit();
    expect(authMock.login).toHaveBeenCalledWith('admin@example.com', 'Password123!');
  });
});
