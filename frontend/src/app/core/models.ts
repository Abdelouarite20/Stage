export type Role = 'ADMIN' | 'MANAGER' | 'AGENT' | 'CLIENT';
export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type TicketStatus =
  | 'NEW'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'WAITING'
  | 'RESOLVED'
  | 'VALIDATED'
  | 'CLOSED'
  | 'REOPENED';
export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'BLOCKED' | 'DONE' | 'CANCELLED';
export type SlaStatus = 'ON_TRACK' | 'OVERDUE' | 'NOT_CONFIGURED' | 'MET' | 'BREACHED';
export type NotificationType =
  | 'ASSIGNMENT'
  | 'SLA_WARNING'
  | 'SLA_OVERDUE'
  | 'TASK_WARNING'
  | 'TASK_OVERDUE'
  | 'UPDATE';

export interface TokenResponse { access_token: string; token_type: string; }
export interface MessageResponse { message: string; }

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: Role;
  customer_id: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: number;
  company_name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Product { id: number; name: string; description: string | null; is_active: boolean; }
export interface ProductModule { id: number; product_id: number; name: string; description: string | null; is_active: boolean; }
export interface Category { id: number; name: string; description: string | null; is_active: boolean; }
export interface SlaConfiguration { id: number; priority: Priority; target_hours: number; warning_threshold_percent: number; is_active: boolean; }

export interface Ticket {
  id: number;
  reference: string;
  customer_id: number;
  subject: string;
  description: string;
  category_id: number;
  module_id: number | null;
  priority: Priority;
  status: TicketStatus;
  creator_id: number;
  assigned_user_id: number | null;
  assigned_user_name: string | null;
  resolution_summary: string | null;
  sla_deadline: string | null;
  sla_status: SlaStatus;
  sla_remaining_minutes: number | null;
  resolved_at: string | null;
  validated_at: string | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketTask {
  id: number;
  ticket_id: number;
  title: string;
  description: string | null;
  assigned_user_id: number | null;
  assigned_user_name: string | null;
  status: TaskStatus;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketComment { id: number; ticket_id: number; author_id: number; author_name: string; content: string; created_at: string; }
export interface HistoryEntry { id: number; ticket_id: number; actor_id: number | null; event_type: string; details: string | null; created_at: string; }
export interface TicketDetail extends Ticket { tasks: TicketTask[]; comments: TicketComment[]; history: HistoryEntry[]; }
export interface TicketPage { items: Ticket[]; total: number; page: number; page_size: number; }

export interface TicketFilters {
  search?: string;
  customer_id?: number;
  status?: TicketStatus;
  priority?: Priority;
  category_id?: number;
  product_id?: number;
  module_id?: number;
  assigned_user_id?: number;
  created_from?: string;
  created_to?: string;
  sla_status?: SlaStatus;
  sort_by?: 'reference' | 'created_at' | 'updated_at' | 'sla_deadline' | 'priority';
  sort_direction?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface DashboardCount { label: string; count: number; }
export interface DashboardSummary {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  overdue_tickets: number;
  sla_compliance_rate: number | null;
  average_resolution_hours: number | null;
  by_status: DashboardCount[];
  by_priority: DashboardCount[];
  by_category: DashboardCount[];
  by_customer: DashboardCount[];
  by_assignee: DashboardCount[];
}

export interface Notification {
  id: number;
  recipient_id: number;
  ticket_id: number | null;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export const ROLES: readonly Role[] = ['ADMIN', 'MANAGER', 'AGENT', 'CLIENT'];
export const PRIORITIES: readonly Priority[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
export const TICKET_STATUSES: readonly TicketStatus[] = ['NEW', 'ASSIGNED', 'IN_PROGRESS', 'WAITING', 'RESOLVED', 'VALIDATED', 'CLOSED', 'REOPENED'];

const LABELS: Readonly<Record<string, string>> = {
  ADMIN: 'Administrateur', MANAGER: 'Responsable', AGENT: 'Agent support', CLIENT: 'Client',
  LOW: 'Faible', MEDIUM: 'Moyenne', HIGH: 'Haute', CRITICAL: 'Critique',
  NEW: 'Nouveau', ASSIGNED: 'Assigné', IN_PROGRESS: 'En cours', WAITING: 'En attente',
  RESOLVED: 'Résolu', VALIDATED: 'Validé', CLOSED: 'Fermé', REOPENED: 'Réouvert',
  TODO: 'À faire', BLOCKED: 'Bloqué', DONE: 'Terminé', CANCELLED: 'Annulé',
  ON_TRACK: 'Dans les temps', OVERDUE: 'En retard', NOT_CONFIGURED: 'Non configuré', MET: 'Respecté', BREACHED: 'Dépassé',
  ASSIGNMENT: 'Affectation', SLA_WARNING: 'Alerte SLA', SLA_OVERDUE: 'SLA dépassé',
  TASK_WARNING: 'Alerte tâche', TASK_OVERDUE: 'Tâche en retard', UPDATE: 'Mise à jour',
};

export function label(value: string | null | undefined): string {
  return value ? (LABELS[value] ?? value.replaceAll('_', ' ')) : '—';
}

export function fullName(user: Pick<User, 'first_name' | 'last_name'>): string {
  return `${user.first_name} ${user.last_name}`.trim();
}
