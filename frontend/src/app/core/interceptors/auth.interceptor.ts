import { HttpErrorResponse, HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { environment } from '../../../environments/environment';
import { AuthService } from '../../auth/services/auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
  ) {}

  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const isApiRequest = req.url.startsWith(environment.apiUrl);
    const accessToken = this.authService.getAccessToken();

    const authorizedRequest = isApiRequest && accessToken
      ? req.clone({
          setHeaders: {
            Authorization: `Bearer ${accessToken}`,
          },
        })
      : req;

    return next.handle(authorizedRequest).pipe(
      catchError((error: unknown) => {
        if (
          isApiRequest &&
          error instanceof HttpErrorResponse &&
          error.status === 401 &&
          this.authService.isAuthenticated()
        ) {
          this.authService.clearSession();
          void this.router.navigate(['/auth/login']);
        }

        return throwError(() => error);
      }),
    );
  }
}
