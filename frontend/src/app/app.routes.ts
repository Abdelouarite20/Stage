import { Routes } from '@angular/router';

import { authGuard, guestGuard, roleGuard } from './core/auth.guard';
import { ShellComponent } from './layout/shell.component';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./pages/login.component').then((m) => m.LoginComponent),
    title: 'Connexion | Alias Support',
  },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      { path: 'dashboard', loadComponent: () => import('./pages/dashboard.component').then((m) => m.DashboardComponent), title: 'Tableau de bord | Alias Support' },
      { path: 'tickets/new', loadComponent: () => import('./pages/ticket-create.component').then((m) => m.TicketCreateComponent), title: 'Nouvelle demande | Alias Support' },
      { path: 'tickets/:id', loadComponent: () => import('./pages/ticket-detail.component').then((m) => m.TicketDetailComponent), title: 'Détail du ticket | Alias Support' },
      { path: 'tickets', loadComponent: () => import('./pages/ticket-list.component').then((m) => m.TicketListComponent), title: 'Tickets | Alias Support' },
      { path: 'customers', loadComponent: () => import('./pages/customers.component').then((m) => m.CustomersComponent), title: 'Clients | Alias Support' },
      { path: 'notifications', loadComponent: () => import('./pages/notifications.component').then((m) => m.NotificationsComponent), title: 'Notifications | Alias Support' },
      { path: 'users', canActivate: [roleGuard], data: { roles: ['ADMIN'] }, loadComponent: () => import('./pages/users.component').then((m) => m.UsersComponent), title: 'Utilisateurs | Alias Support' },
      { path: 'configuration', canActivate: [roleGuard], data: { roles: ['ADMIN'] }, loadComponent: () => import('./pages/configuration.component').then((m) => m.ConfigurationComponent), title: 'Configuration | Alias Support' },
    ],
  },
  { path: '**', loadComponent: () => import('./pages/not-found.component').then((m) => m.NotFoundComponent), title: 'Page introuvable | Alias Support' },
];
