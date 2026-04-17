import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../../../auth/services/auth.service';

@Component({
  selector: 'app-painel-redirect',
  template: '',
})
export class PainelRedirectComponent implements OnInit {
  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    void this.router.navigate(this.authService.getPostLoginRoute());
  }
}
