import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { apiErrorMessage } from '../core/api-error';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import {
  Category,
  Customer,
  PRIORITIES,
  Priority,
  ProductModule,
  TaskStatus,
  TicketDetail,
  TicketStatus,
  TicketTask,
  User,
  label,
} from '../core/models';

const TICKET_TRANSITIONS: Readonly<Record<TicketStatus, readonly TicketStatus[]>> = {
  NEW: [],
  ASSIGNED: ['IN_PROGRESS'],
  IN_PROGRESS: ['WAITING', 'RESOLVED'],
  WAITING: ['IN_PROGRESS'],
  RESOLVED: ['VALIDATED', 'IN_PROGRESS'],
  VALIDATED: ['CLOSED'],
  CLOSED: ['REOPENED'],
  REOPENED: ['IN_PROGRESS'],
};

const TASK_TRANSITIONS: Readonly<Record<TaskStatus, readonly TaskStatus[]>> = {
  TODO: ['IN_PROGRESS', 'CANCELLED'],
  IN_PROGRESS: ['BLOCKED', 'DONE', 'CANCELLED'],
  BLOCKED: ['IN_PROGRESS', 'CANCELLED'],
  DONE: [],
  CANCELLED: [],
};

@Component({
  selector: 'app-ticket-detail',
  imports: [DatePipe, ReactiveFormsModule, RouterLink],
  template: `
    <header class="page-header compact-header">
      <div><a class="back-link" routerLink="/tickets">← Retour aux tickets</a>@if (ticket(); as item) { <div class="title-row"><h1>{{ item.subject }}</h1><span class="badge" [class]="'badge status-' + item.status.toLowerCase()">{{ displayLabel(item.status) }}</span></div><p>{{ item.reference }} · Créé le {{ item.created_at | date:'dd/MM/yyyy à HH:mm' }}</p> }</div>
    </header>
    @if (error()) { <div class="alert alert-error">{{ error() }}</div> }
    @if (success()) { <div class="alert alert-success">{{ success() }}</div> }
    @if (loading()) {
      <div class="loading-card">Chargement du ticket…</div>
    } @else if (ticket(); as item) {
      <div class="detail-layout">
        <div class="detail-main">
          <section class="panel detail-card">
            <div class="panel-header"><div><h2>Description</h2><p>Informations communiquées lors de la création</p></div></div>
            <p class="long-text">{{ item.description }}</p>
            @if (item.resolution_summary) { <div class="resolution-box"><strong>Solution apportée</strong><p>{{ item.resolution_summary }}</p></div> }
          </section>

          <section class="panel detail-card">
            <div class="panel-header"><div><h2>Suivi du ticket</h2><p>Faites progresser la demande selon le workflow.</p></div></div>
            @if (availableStatuses().length) {
              <form class="inline-action-form status-form" [formGroup]="statusForm" (ngSubmit)="changeStatus()">
                <label>Prochaine étape<select formControlName="status"><option value="">Choisir…</option>@for (status of availableStatuses(); track status) { <option [value]="status">{{ displayLabel(status) }}</option> }</select></label>
                @if (statusForm.controls.status.value === 'RESOLVED') { <label class="span-full">Résumé de résolution <span class="required">*</span><textarea formControlName="resolution_summary" rows="3" maxlength="10000" placeholder="Décrivez la solution mise en place…"></textarea></label> }
                <label class="span-full">Note interne @if (noteRequired()) { <span class="required">*</span> } @else { (facultative) }<textarea formControlName="note" rows="2" maxlength="2000" placeholder="Contexte utile pour cette transition…"></textarea>@if (noteRequired()) { <small>Une justification est requise pour l'attente, la réouverture ou le rejet d'une résolution.</small> }</label>
                <button class="button button-primary" type="submit" [disabled]="actionLoading() || !statusForm.controls.status.value">Mettre à jour</button>
              </form>
            } @else {
              <p class="muted">Aucune transition n'est disponible pour votre rôle à cette étape.</p>
            }
          </section>

          <section class="panel detail-card">
            <div class="panel-header"><div><h2>Commentaires</h2><p>{{ item.comments.length }} échange(s)</p></div></div>
            <div class="comment-list">
              @for (comment of item.comments; track comment.id) {
                <article class="comment"><span class="avatar avatar-small">{{ authorInitials(comment.author_id, comment.author_name) }}</span><div><div><strong>{{ comment.author_name || userName(comment.author_id) }}</strong><time>{{ comment.created_at | date:'dd/MM/yyyy à HH:mm' }}</time></div><p>{{ comment.content }}</p></div></article>
              } @empty { <p class="empty-state">Aucun commentaire pour le moment.</p> }
            </div>
            <form class="comment-form" [formGroup]="commentForm" (ngSubmit)="addComment()"><label class="sr-only">Ajouter un commentaire</label><textarea formControlName="content" rows="3" maxlength="10000" placeholder="Ajouter une information ou poser une question…"></textarea><button class="button button-primary" type="submit" [disabled]="commentForm.invalid || actionLoading()">Publier</button></form>
          </section>

          @if (!isClient()) {
            <section class="panel detail-card">
              <div class="panel-header"><div><h2>Tâches</h2><p>Travail interne lié à ce ticket</p></div></div>
              <div class="task-list">
                @for (task of item.tasks; track task.id) {
                  <article class="task-row"><span class="task-check" [class.done]="task.status === 'DONE'">✓</span><div><strong>{{ task.title }}</strong><p>{{ task.description || 'Aucune description' }}</p><small>{{ task.assigned_user_name || userName(task.assigned_user_id) }} @if (task.due_date) { · Échéance {{ task.due_date | date:'dd/MM/yyyy HH:mm' }} }</small></div><span class="badge">{{ displayLabel(task.status) }}</span>@if (nextTaskStatuses(task.status).length) { <div class="task-transition"><input #taskNote maxlength="2000" placeholder="Note si blocage/annulation" aria-label="Note de changement de statut"><select class="compact-select" [value]="task.status" #taskStatus (change)="changeTaskStatus(task, taskStatus.value, taskNote.value); taskStatus.value = task.status"><option [value]="task.status" disabled>Action…</option>@for (status of nextTaskStatuses(task.status); track status) { <option [value]="status">{{ displayLabel(status) }}</option> }</select></div> }</article>
                } @empty { <p class="empty-state">Aucune tâche. Ajoutez la première étape de travail.</p> }
              </div>
              @if (canCreateTask()) { <details class="creation-details"><summary>+ Ajouter une tâche</summary>
                <form class="form-grid two-columns compact-form" [formGroup]="taskForm" (ngSubmit)="createTask()">
                  <label>Titre <span class="required">*</span><input formControlName="title" maxlength="250"></label>
                  <label>Responsable<select formControlName="assigned_user_id"><option [ngValue]="null">Non affecté</option>@for (user of taskAssignees(); track user.id) { <option [ngValue]="user.id">{{ user.first_name }} {{ user.last_name }}</option> }</select></label>
                  <label class="span-full">Description<textarea formControlName="description" rows="2" maxlength="10000"></textarea></label>
                  <label>Échéance<input type="datetime-local" formControlName="due_date"></label>
                  <div class="form-submit"><button class="button button-primary" type="submit" [disabled]="taskForm.invalid || actionLoading()">Créer la tâche</button></div>
                </form>
              </details> }
            </section>
          }

          <section class="panel detail-card">
            <div class="panel-header"><div><h2>Historique</h2><p>Traçabilité des événements importants</p></div></div>
            <div class="timeline">
              @for (entry of item.history; track entry.id) { <article><i></i><div><strong>{{ eventLabel(entry.event_type) }}</strong><p>{{ userName(entry.actor_id) }} · {{ entry.created_at | date:'dd/MM/yyyy à HH:mm' }}</p>@if (historyNote(entry.details); as note) { <small class="history-note">{{ note }}</small> }</div></article> }
            </div>
          </section>
        </div>

        <aside class="detail-aside">
          <section class="panel metadata-card"><h2>Informations</h2><dl><div><dt>Client</dt><dd>{{ customerName(item.customer_id) }}</dd></div><div><dt>Catégorie</dt><dd>{{ categoryName(item.category_id) }}</dd></div><div><dt>Module</dt><dd>{{ moduleName(item.module_id) }}</dd></div><div><dt>Priorité</dt><dd><span class="priority" [class]="'priority-' + item.priority.toLowerCase()"><i></i>{{ displayLabel(item.priority) }}</span></dd></div><div><dt>Intervenant</dt><dd>{{ item.assigned_user_name || userName(item.assigned_user_id) }}</dd></div><div><dt>Dernière mise à jour</dt><dd>{{ item.updated_at | date:'dd/MM/yyyy HH:mm' }}</dd></div></dl></section>
          <section class="panel sla-card" [class.sla-card-overdue]="item.sla_status === 'OVERDUE' || item.sla_status === 'BREACHED'"><span class="eyebrow">ENGAGEMENT SLA</span><strong>{{ slaText(item.sla_status, item.sla_remaining_minutes) }}</strong><p>@if (item.sla_deadline) { Échéance : {{ item.sla_deadline | date:'dd/MM/yyyy à HH:mm' }} } @else { Aucune règle active pour cette priorité. }</p></section>
          @if (canManage()) {
            @if (item.status !== 'CLOSED' && item.status !== 'VALIDATED') { <section class="panel action-card"><h2>Affectation</h2><form [formGroup]="assignmentForm" (ngSubmit)="assign()"><label>Intervenant<select formControlName="assigned_user_id"><option [ngValue]="0" disabled>Choisir…</option>@for (user of taskAssignees(); track user.id) { <option [ngValue]="user.id">{{ user.first_name }} {{ user.last_name }}</option> }</select></label><button class="button button-secondary button-block" type="submit" [disabled]="assignmentForm.invalid || actionLoading()">Affecter</button></form></section> }
            @if (item.status !== 'CLOSED') { <section class="panel action-card"><h2>Priorité</h2><form [formGroup]="priorityForm" (ngSubmit)="changePriority()"><label>Urgence<select formControlName="priority">@for (priority of priorities; track priority) { <option [ngValue]="priority">{{ displayLabel(priority) }}</option> }</select></label><button class="button button-secondary button-block" type="submit" [disabled]="actionLoading()">Modifier</button></form></section> }
          }
        </aside>
      </div>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketDetailComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  readonly priorities = PRIORITIES;
  readonly ticket = signal<TicketDetail | null>(null);
  readonly customers = signal<Customer[]>([]);
  readonly categories = signal<Category[]>([]);
  readonly modules = signal<ProductModule[]>([]);
  readonly users = signal<User[]>([]);
  readonly loading = signal(true);
  readonly actionLoading = signal(false);
  readonly error = signal('');
  readonly success = signal('');
  readonly ticketId = Number(this.route.snapshot.paramMap.get('id'));
  readonly isClient = computed(() => this.auth.user()?.role === 'CLIENT');
  readonly canManage = computed(() => this.auth.hasAnyRole('ADMIN', 'MANAGER'));
  readonly taskAssignees = computed(() => this.users().filter((user) => user.is_active && (user.role === 'AGENT' || user.role === 'MANAGER')));
  readonly assignmentForm = this.fb.nonNullable.group({ assigned_user_id: [0, Validators.min(1)] });
  readonly priorityForm = this.fb.nonNullable.group({ priority: this.fb.nonNullable.control<Priority>('MEDIUM') });
  readonly statusForm = this.fb.nonNullable.group({ status: this.fb.nonNullable.control<TicketStatus | ''>(''), resolution_summary: '', note: '' });
  readonly commentForm = this.fb.nonNullable.group({ content: ['', [Validators.required, Validators.maxLength(10000)]] });
  readonly taskForm = this.fb.group({
    title: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(250)]),
    description: this.fb.nonNullable.control(''),
    assigned_user_id: this.fb.control<number | null>(null),
    due_date: this.fb.nonNullable.control(''),
  });

  ngOnInit(): void {
    if (!Number.isInteger(this.ticketId) || this.ticketId < 1) { this.error.set('Identifiant de ticket invalide.'); this.loading.set(false); return; }
    this.loadLookups();
    this.loadTicket();
  }

  loadLookups(): void {
    this.api.customers('', false).subscribe({ next: (items) => this.customers.set(items) });
    this.api.categories(false).subscribe({ next: (items) => this.categories.set(items) });
    this.api.modules(undefined, false).subscribe({ next: (items) => this.modules.set(items) });
    if (this.auth.hasAnyRole('ADMIN', 'MANAGER')) {
      this.api.users({ active_only: false }).subscribe({ next: (items) => this.users.set(items) });
    } else if (this.auth.user()) {
      this.users.set([this.auth.user()!]);
    }
  }

  loadTicket(message = ''): void {
    this.api.ticket(this.ticketId).subscribe({
      next: (item) => {
        // The backend guarantees an empty task collection for CLIENT accounts.
        this.ticket.set(item);
        this.assignmentForm.controls.assigned_user_id.setValue(item.assigned_user_id ?? 0);
        this.priorityForm.controls.priority.setValue(item.priority);
        this.loading.set(false);
        this.actionLoading.set(false);
        this.success.set(message);
      },
      error: (error: unknown) => { this.error.set(apiErrorMessage(error)); this.loading.set(false); this.actionLoading.set(false); },
    });
  }

  availableStatuses(): readonly TicketStatus[] {
    const item = this.ticket();
    if (!item || this.isClient()) return [];
    const next = TICKET_TRANSITIONS[item.status];
    if (this.auth.hasAnyRole('AGENT')) return next.filter((status) => ['IN_PROGRESS', 'WAITING', 'RESOLVED'].includes(status));
    return next;
  }

  assign(): void {
    if (this.assignmentForm.invalid) return;
    this.runAction(this.api.assignTicket(this.ticketId, this.assignmentForm.getRawValue().assigned_user_id), 'Ticket affecté.');
  }

  changePriority(): void {
    this.runAction(this.api.changePriority(this.ticketId, this.priorityForm.getRawValue().priority), 'Priorité mise à jour.');
  }

  changeStatus(): void {
    const { status, resolution_summary, note } = this.statusForm.getRawValue();
    if (!status) return;
    if (status === 'RESOLVED' && !resolution_summary.trim()) { this.error.set('Le résumé de résolution est obligatoire.'); return; }
    if (this.noteRequired() && !note.trim()) { this.error.set('Une note est obligatoire pour cette transition.'); return; }
    this.actionLoading.set(true);
    this.error.set('');
    this.api.changeStatus(this.ticketId, status, resolution_summary.trim(), note.trim()).subscribe({
      next: () => { this.statusForm.reset(); this.loadTicket('Statut mis à jour.'); },
      error: (error: unknown) => this.actionFailed(error),
    });
  }

  addComment(): void {
    if (this.commentForm.invalid) return;
    this.actionLoading.set(true);
    this.api.addComment(this.ticketId, this.commentForm.getRawValue().content.trim()).subscribe({
      next: () => { this.commentForm.reset(); this.loadTicket('Commentaire ajouté.'); },
      error: (error: unknown) => this.actionFailed(error),
    });
  }

  createTask(): void {
    if (this.taskForm.invalid || this.isClient()) return;
    const value = this.taskForm.getRawValue();
    this.actionLoading.set(true);
    this.api.createTask(this.ticketId, {
      title: value.title.trim(), description: value.description.trim() || null,
      assigned_user_id: value.assigned_user_id, due_date: value.due_date ? new Date(value.due_date).toISOString() : null,
    }).subscribe({
      next: () => { this.taskForm.reset(); this.loadTicket('Tâche créée.'); },
      error: (error: unknown) => this.actionFailed(error),
    });
  }

  changeTaskStatus(task: TicketTask, value: string, note: string): void {
    if (!TASK_TRANSITIONS[task.status].includes(value as TaskStatus)) return;
    if ((value === 'BLOCKED' || value === 'CANCELLED') && !note.trim()) { this.error.set('Une note est obligatoire pour bloquer ou annuler une tâche.'); return; }
    this.actionLoading.set(true);
    this.api.updateTask(task.id, value as TaskStatus, note.trim()).subscribe({ next: () => this.loadTicket('Tâche mise à jour.'), error: (error: unknown) => this.actionFailed(error) });
  }

  private runAction(request: ReturnType<ApiService['assignTicket']>, message: string): void {
    this.actionLoading.set(true);
    this.error.set(''); this.success.set('');
    request.pipe(finalize(() => this.actionLoading.set(false))).subscribe({ next: () => this.loadTicket(message), error: (error: unknown) => this.actionFailed(error) });
  }

  private actionFailed(error: unknown): void { this.error.set(apiErrorMessage(error)); this.actionLoading.set(false); }
  displayLabel(value: string): string { return label(value); }
  noteRequired(): boolean {
    const target = this.statusForm.controls.status.value;
    return target === 'WAITING' || target === 'REOPENED' || (this.ticket()?.status === 'RESOLVED' && target === 'IN_PROGRESS');
  }
  canCreateTask(): boolean { return !this.isClient() && !['VALIDATED', 'CLOSED'].includes(this.ticket()?.status ?? ''); }
  nextTaskStatuses(status: TaskStatus): readonly TaskStatus[] { return this.auth.hasAnyRole('AGENT') ? TASK_TRANSITIONS[status].filter((value) => value !== 'CANCELLED') : TASK_TRANSITIONS[status]; }
  customerName(id: number): string { return this.customers().find((item) => item.id === id)?.company_name ?? `Client #${id}`; }
  categoryName(id: number): string { return this.categories().find((item) => item.id === id)?.name ?? `Catégorie #${id}`; }
  moduleName(id: number | null): string { return id ? (this.modules().find((item) => item.id === id)?.name ?? `Module #${id}`) : '—'; }
  userName(id: number | null): string { const user = this.users().find((item) => item.id === id); return user ? `${user.first_name} ${user.last_name}` : id ? `Utilisateur #${id}` : 'Système'; }
  authorInitials(id: number, name: string): string { const user = this.users().find((item) => item.id === id); const source = user ? `${user.first_name} ${user.last_name}` : name; return source.split(/\s+/).slice(0, 2).map((part) => part[0] ?? '').join('').toUpperCase() || '?'; }
  eventLabel(event: string): string { return label(event.replace('STATUS_', 'Statut : ').replaceAll('_', ' ')); }
  historyNote(details: string | null): string {
    if (!details) return '';
    try {
      const parsed = JSON.parse(details) as { note?: unknown };
      return typeof parsed.note === 'string' ? parsed.note : '';
    } catch {
      return '';
    }
  }
  slaText(status: string, minutes: number | null): string {
    if (status === 'NOT_CONFIGURED') return 'SLA non configuré';
    if (status === 'MET') return 'SLA respecté';
    if (status === 'BREACHED') return 'SLA dépassé';
    if (minutes === null) return label(status);
    const hours = Math.floor(Math.abs(minutes) / 60); const mins = Math.abs(minutes) % 60;
    return status === 'OVERDUE' ? `En retard de ${hours} h ${mins} min` : `${hours} h ${mins} min restantes`;
  }
}
