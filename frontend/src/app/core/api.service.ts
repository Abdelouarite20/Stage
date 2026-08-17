import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Category,
  Customer,
  DashboardSummary,
  MessageResponse,
  Notification,
  Priority,
  Product,
  ProductModule,
  Role,
  SlaConfiguration,
  TaskStatus,
  Ticket,
  TicketComment,
  TicketDetail,
  TicketFilters,
  TicketPage,
  TicketStatus,
  TicketTask,
  User,
} from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  dashboard(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>('/api/dashboard/summary');
  }

  tickets(filters: TicketFilters = {}): Observable<TicketPage> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== null && value !== '') params = params.set(key, String(value));
    }
    return this.http.get<TicketPage>('/api/tickets', { params });
  }

  ticket(id: number): Observable<TicketDetail> {
    return this.http.get<TicketDetail>(`/api/tickets/${id}`);
  }

  createTicket(payload: { customer_id: number; subject: string; description: string; category_id: number; module_id: number | null; priority: Priority }): Observable<Ticket> {
    return this.http.post<Ticket>('/api/tickets', payload);
  }

  assignTicket(id: number, assigned_user_id: number): Observable<Ticket> {
    return this.http.post<Ticket>(`/api/tickets/${id}/assign`, { assigned_user_id });
  }

  changePriority(id: number, priority: Priority): Observable<Ticket> {
    return this.http.post<Ticket>(`/api/tickets/${id}/priority`, { priority });
  }

  changeStatus(id: number, status: TicketStatus, resolution_summary?: string, note?: string): Observable<Ticket> {
    return this.http.post<Ticket>(`/api/tickets/${id}/status`, {
      status,
      resolution_summary: resolution_summary || null,
      note: note || null,
    });
  }

  addComment(ticketId: number, content: string): Observable<TicketComment> {
    return this.http.post<TicketComment>(`/api/tickets/${ticketId}/comments`, { content });
  }

  createTask(ticketId: number, payload: { title: string; description: string | null; assigned_user_id: number | null; due_date: string | null }): Observable<TicketTask> {
    return this.http.post<TicketTask>(`/api/tickets/${ticketId}/tasks`, payload);
  }

  updateTask(taskId: number, status: TaskStatus, note?: string): Observable<TicketTask> {
    return this.http.patch<TicketTask>(`/api/tasks/${taskId}`, { status, note: note || null });
  }

  customers(search = '', activeOnly = true): Observable<Customer[]> {
    return this.http.get<Customer[]>('/api/customers', { params: { search, active_only: activeOnly } });
  }

  createCustomer(payload: { company_name: string; contact_name: string | null; email: string | null; phone: string | null; address: string | null }): Observable<Customer> {
    return this.http.post<Customer>('/api/customers', payload);
  }

  updateCustomer(id: number, payload: Partial<Customer>): Observable<Customer> {
    return this.http.patch<Customer>(`/api/customers/${id}`, payload);
  }

  users(options: { search?: string; role?: Role; active_only?: boolean } = {}): Observable<User[]> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(options)) {
      if (value !== undefined && value !== '') params = params.set(key, String(value));
    }
    return this.http.get<User[]>('/api/users', { params });
  }

  createUser(payload: { first_name: string; last_name: string; email: string; password: string; role: Role; customer_id: number | null; is_active: boolean }): Observable<User> {
    return this.http.post<User>('/api/users', payload);
  }

  updateUser(id: number, payload: Partial<User>): Observable<User> {
    return this.http.patch<User>(`/api/users/${id}`, payload);
  }

  products(activeOnly = true): Observable<Product[]> {
    return this.http.get<Product[]>('/api/catalog/products', { params: { active_only: activeOnly } });
  }

  modules(productId?: number, activeOnly = true): Observable<ProductModule[]> {
    let params = new HttpParams().set('active_only', String(activeOnly));
    if (productId !== undefined) params = params.set('product_id', productId);
    return this.http.get<ProductModule[]>('/api/catalog/modules', { params });
  }

  categories(activeOnly = true): Observable<Category[]> {
    return this.http.get<Category[]>('/api/catalog/categories', { params: { active_only: activeOnly } });
  }

  createProduct(payload: { name: string; description: string | null }): Observable<Product> {
    return this.http.post<Product>('/api/catalog/products', payload);
  }

  updateProduct(id: number, payload: Partial<Product>): Observable<Product> {
    return this.http.patch<Product>(`/api/catalog/products/${id}`, payload);
  }

  createModule(payload: { product_id: number; name: string; description: string | null }): Observable<ProductModule> {
    return this.http.post<ProductModule>('/api/catalog/modules', payload);
  }

  updateModule(id: number, payload: Partial<ProductModule>): Observable<ProductModule> {
    return this.http.patch<ProductModule>(`/api/catalog/modules/${id}`, payload);
  }

  createCategory(payload: { name: string; description: string | null }): Observable<Category> {
    return this.http.post<Category>('/api/catalog/categories', payload);
  }

  updateCategory(id: number, payload: Partial<Category>): Observable<Category> {
    return this.http.patch<Category>(`/api/catalog/categories/${id}`, payload);
  }

  slaConfigurations(): Observable<SlaConfiguration[]> {
    return this.http.get<SlaConfiguration[]>('/api/catalog/sla');
  }

  saveSla(priority: Priority, payload: { target_hours: number; warning_threshold_percent: number; is_active: boolean }): Observable<SlaConfiguration> {
    return this.http.put<SlaConfiguration>(`/api/catalog/sla/${priority}`, payload);
  }

  notifications(unreadOnly = false): Observable<Notification[]> {
    return this.http.get<Notification[]>('/api/notifications', { params: { unread_only: unreadOnly, limit: 100 } });
  }

  unreadCount(): Observable<{ count: number }> {
    return this.http.get<{ count: number }>('/api/notifications/unread-count');
  }

  readNotification(id: number): Observable<Notification> {
    return this.http.post<Notification>(`/api/notifications/${id}/read`, {});
  }

  readAllNotifications(): Observable<MessageResponse> {
    return this.http.post<MessageResponse>('/api/notifications/read-all', {});
  }
}
