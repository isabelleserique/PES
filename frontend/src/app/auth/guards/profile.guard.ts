import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, UrlTree } from '@angular/router';

import { AuthService, UserPerfil } from '../services/auth.service';

@Injectable({ providedIn: 'root' })
export class ProfileGuard implements CanActivate {
  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
  ) {}

  canActivate(route: ActivatedRouteSnapshot): boolean | UrlTree {
    const requiredPerfil = route.data['perfil'] as UserPerfil | undefined;
    const currentPerfil = this.authService.getStoredPerfil();

    if (!currentPerfil) {
      return this.router.createUrlTree(['/auth/login']);
    }

    if (!requiredPerfil || currentPerfil === requiredPerfil) {
      return true;
    }

    return this.router.createUrlTree(this.authService.getPostLoginRoute());
  }
}
