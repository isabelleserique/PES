import { Component } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

import { AuthService } from '../../../auth/services/auth.service';
import { getApiErrorMessage } from '../../../auth/utils/api-error.util';
import { BuscarTccParams, PublicoService, TccPublico } from '../../services/publico.service';

interface ProfessorPublico {
  nome: string;
  titulo: string;
  objetosEstudo: string[];
  descricao: string;
  foto: string;
  fotoUrl: string;
  email: string;
  lattes: string;
}

const ICOMP_PROFESSORES: ProfessorPublico[] = [
  {
    nome: 'Alberto Nogueira de Castro Jr',
    titulo: 'Informática na Educação e Inteligência Artificial',
    descricao: 'Ph.D. - University of Edinburgh',
    foto: 'AN',
    fotoUrl: 'https://icomp.ufam.edu.br/images/alberto.jpg',
    email: 'alberto@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/5919189481858271',
    objetosEstudo: ['Informática na Educação e Inteligência Artificial'],
  },
  {
    nome: 'Alexandre Passito de Queiroz',
    titulo: 'Redes de Computadores',
    descricao: 'Doutorado - Universidade Federal do Amazonas',
    foto: 'AP',
    fotoUrl: 'https://icomp.ufam.edu.br/images/passito.jpg',
    email: 'passito@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/7507000181049352',
    objetosEstudo: [
      'Redes de Computadores e Internet',
      'Cybersegurança',
      'Aprendizagem de Máquina Aplicada',
    ],
  },
  {
    nome: 'Altigran Soares da Silva',
    titulo: 'Banco de Dados e Recuperação de Informação',
    descricao: 'Doutorado - Universidade Federal de Minas Gerais',
    foto: 'AS',
    fotoUrl: 'https://icomp.ufam.edu.br/images/altigran.jpeg',
    email: 'alti@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/3405503472010994',
    objetosEstudo: [
      'Gerência de Dados',
      'Recuperação de Informação',
      'Mineração de Dados',
      'Modelos de Linguagem',
    ],
  },
  {
    nome: 'Ana Carolina Oran Rocha',
    titulo: 'Engenharia de Software',
    descricao: 'Doutorado - Universidade Federal do Amazonas',
    foto: 'AC',
    fotoUrl: 'https://icomp.ufam.edu.br/images/Ana.jpg',
    email: 'ana.oran@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/4158615534347398',
    objetosEstudo: [
      'Engenharia de Requisitos',
      'Educação em Engenharia de Software',
      'Testes',
      'UX',
    ],
  },
  {
    nome: 'André Luiz Carvalho',
    titulo: 'Banco de Dados e Recuperação de Informação',
    descricao: 'Doutorado - Universidade Federal do Amazonas',
    foto: 'AL',
    fotoUrl: 'https://icomp.ufam.edu.br/images/andre.jpg',
    email: 'andre@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/4863447798119856',
    objetosEstudo: [
      'Processamento de Linguagem Natural',
      'Aprendizagem Profunda',
      'Mineração de Dados',
      'Redes Sociais',
    ],
  },
  {
    nome: 'Bruno Freitas Gadelha',
    titulo: 'Engenharia de Software',
    descricao: 'Doutorado - Pontifícia Universidade Católica do Rio de Janeiro',
    foto: 'BF',
    fotoUrl: 'https://icomp.ufam.edu.br/images/bruno.jpg',
    email: 'bruno@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/4987487225451219',
    objetosEstudo: ['Seleção de Tecnologias de Software', 'Teste Baseado em Modelos'],
  },
  {
    nome: 'César Augusto Viana Melo',
    titulo: 'Redes de Computadores',
    descricao: 'Doutorado - Universidade Estadual de Campinas',
    foto: 'CA',
    fotoUrl: 'https://icomp.ufam.edu.br/images/cesar.jpg',
    email: 'cavmelo@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/0097703442306179',
    objetosEstudo: ['Redes de Computadores'],
  },
  {
    nome: 'David Braga Fernandes de Oliveira',
    titulo: 'Banco de Dados e Recuperação de Informação',
    descricao: 'Doutorado - Universidade Federal de Minas Gerais',
    foto: 'DB',
    fotoUrl: 'https://icomp.ufam.edu.br/images/david.jpg',
    email: 'david@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/9561812825173697',
    objetosEstudo: [
      'Educação em Computação',
      'Learning Analytics',
      'Métricas de Avaliação Estudantil',
      'Juízes Online',
    ],
  },
  {
    nome: 'Edjair de Souza Mota',
    titulo: 'Redes de Computadores',
    descricao: 'Doutorado - Technische Universitaet Berlin',
    foto: 'ES',
    fotoUrl: 'https://icomp.ufam.edu.br/images/edjair.jpg',
    email: 'edjair@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/5771638576099195',
    objetosEstudo: ['Internet das Coisas', 'Sustentabilidade'],
  },
  {
    nome: 'Edjard de Souza Mota',
    titulo: 'Inteligência Artificial e Linguagens Formais',
    descricao: 'Doutorado - Universidade de Edimburgo',
    foto: 'ES',
    fotoUrl: 'https://icomp.ufam.edu.br/images/edjard.jpg',
    email: 'edjard@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/0757666181169076',
    objetosEstudo: ['IA NeuroSimbólica', 'Métodos Formais', 'IA Confiável', 'Fintechs'],
  },
  {
    nome: 'Eulanda Miranda dos Santos',
    titulo: 'Visão Computacional e Robótica',
    descricao: 'Doutorado - Université du Quebec',
    foto: 'EM',
    fotoUrl: 'https://icomp.ufam.edu.br/images/eulanda.jpg',
    email: 'emsantos@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/3054990742969890',
    objetosEstudo: ['Visão Computacional', 'Robótica'],
  },
  {
    nome: 'Edleno Silva de Moura',
    titulo: 'Banco de Dados e Recuperação de Informação',
    descricao: 'Doutorado - Universidade Federal de Minas Gerais',
    foto: 'ES',
    fotoUrl: 'https://icomp.ufam.edu.br/images/edleno.jpg',
    email: 'edleno@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/4737852130924504',
    objetosEstudo: ['Recuperação de Informação', 'Sistemas de Busca', 'Bioinformática'],
  },
  {
    nome: 'Edson Nascimento Silva-Jr',
    titulo: 'Redes de Computadores',
    descricao: 'Doutorado - Universidade Federal do Rio Grande do Sul',
    foto: 'EN',
    fotoUrl: 'https://icomp.ufam.edu.br/images/edson.jpg',
    email: 'edson@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/6012757443739680',
    objetosEstudo: ['Gerenciamento de Redes', 'Segurança de Redes', 'Saúde Digital'],
  },
  {
    nome: 'Eduardo Freire Nakamura',
    titulo: 'Redes de Computadores',
    descricao: 'Doutorado - Universidade Federal de Minas Gerais',
    foto: 'EF',
    fotoUrl: 'https://icomp.ufam.edu.br/images/eduardonaka.jpg',
    email: 'nakamura@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/1448696292042915',
    objetosEstudo: ['Redes de Computadores'],
  },
  {
    nome: 'Eduardo James Pereira Souto',
    titulo: 'Redes de Computadores e Sistemas Distribuídos',
    descricao: 'Doutorado - Universidade Federal de Pernambuco',
    foto: 'EJ',
    fotoUrl: 'https://icomp.ufam.edu.br/images/eduardo.jpg',
    email: 'esouto@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/3875301617975895',
    objetosEstudo: ['E-Health', 'Internet das Coisas', 'Segurança de Sistemas'],
  },
  {
    nome: 'Eduardo Luzeiro Feitosa',
    titulo: 'Redes de Computadores',
    descricao: 'Doutorado - Universidade Federal de Pernambuco',
    foto: 'EL',
    fotoUrl: 'https://icomp.ufam.edu.br/images/eduardofeitosa.jpg',
    email: 'efeitosa@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/5939944067207881',
    objetosEstudo: ['Segurança Web', 'Privacidade', 'Malware Android', 'IA aplicada à Segurança'],
  },
  {
    nome: 'Elaine Harada Teixeira de Oliveira',
    titulo: 'Software, Interação e Aplicações',
    descricao: 'Doutorado - Universidade Federal do Rio Grande do Sul',
    foto: 'EH',
    fotoUrl: 'https://icomp.ufam.edu.br/images/elaine.jpg',
    email: 'elaine@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/6553721651836761',
    objetosEstudo: ['Informática na Educação', 'Inteligência Artificial'],
  },
  {
    nome: 'Fabíola Guerra Nakamura',
    titulo: 'Otimização, Algoritmos e Complexidade Computacional',
    descricao: 'Doutorado - Universidade Federal de Minas Gerais',
    foto: 'FG',
    fotoUrl: 'https://icomp.ufam.edu.br/images/fabiola.jpg',
    email: 'fabiola@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/9615041048900531',
    objetosEstudo: ['Otimização', 'Algoritmos', 'Complexidade Computacional'],
  },
  {
    nome: 'Horácio Antonio Braga Fernandes de Oliveira',
    titulo: 'Redes de Computadores',
    descricao: 'Doutorado - Universidade Federal de Minas Gerais',
    foto: 'HA',
    fotoUrl: 'https://icomp.ufam.edu.br/images/horacio.jpg',
    email: 'horacio@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/9314744999783676',
    objetosEstudo: ['Localização Indoor', 'Android/AOSP', 'Internet das Coisas', 'Redes Sem Fio'],
  },
  {
    nome: 'João Marcos Bastos Cavalcanti',
    titulo: 'Banco de Dados e Recuperação de Informação',
    descricao: 'Doutorado - Universidade de Edimburgo',
    foto: 'JM',
    fotoUrl: 'https://icomp.ufam.edu.br/images/joao.jpg',
    email: 'john@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/3537707069694606',
    objetosEstudo: ['Processamento de Imagens', 'Recuperação de Informação com Imagens'],
  },
  {
    nome: 'José Francisco de Magalhães Netto',
    titulo: 'Informática na Educação e Inteligência Artificial',
    descricao: 'Doutorado - Universidade Federal do Rio de Janeiro',
    foto: 'JF',
    fotoUrl: 'https://icomp.ufam.edu.br/images/josef.jpg',
    email: 'jnetto@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/3958238119785924',
    objetosEstudo: ['IA aplicada à Educação', 'Ciência de Dados', 'Robótica Educacional', 'Games Educacionais'],
  },
  {
    nome: 'José Luiz de Souza Pio',
    titulo: 'Visão Computacional e Robótica',
    descricao: 'Doutorado - Universidade Federal do Rio de Janeiro',
    foto: 'JL',
    fotoUrl: 'https://icomp.ufam.edu.br/images/josepio.jpg',
    email: 'josepio@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/1014904168887285',
    objetosEstudo: ['Visão Computacional', 'Robótica Inteligente', 'Computação Gráfica'],
  },
  {
    nome: 'José Reginaldo Hughes Carvalho',
    titulo: 'Visão Computacional e Robótica',
    descricao: 'Doutorado - Universidade Estadual de Campinas',
    foto: 'JR',
    fotoUrl: 'https://icomp.ufam.edu.br/images/joserei.jpg',
    email: 'reginaldo@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/3161958119304780',
    objetosEstudo: ['Robótica Móvel', 'Percepção Robótica', 'Aprendizagem por Reforço', 'Navegação Robótica'],
  },
  {
    nome: 'Juan Colonna',
    titulo: 'Inteligência Artificial e Ciência de Dados',
    descricao: 'Doutorado - Universidade Federal do Amazonas',
    foto: 'JC',
    fotoUrl: 'https://icomp.ufam.edu.br/images/juan.jpeg',
    email: 'juancolonna@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/9535853909210803',
    objetosEstudo: ['Aprendizagem de Máquina'],
  },
  {
    nome: 'Ketlen Karine Teles Lucena',
    titulo: 'Informática na Educação',
    descricao: 'Doutorado - Universidade Federal do Amazonas',
    foto: 'KK',
    fotoUrl: 'https://icomp.ufam.edu.br/images/KetlenK.jpeg',
    email: 'ketlen.teles@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/4814971319638846',
    objetosEstudo: ['Informática na Educação', 'Gamificação', 'Educação em Computação', 'IA'],
  },
  {
    nome: 'Leandro Silva Galvão de Carvalho',
    titulo: 'Redes de Computadores',
    descricao: 'Doutorado - Universidade Federal do Amazonas',
    foto: 'LS',
    fotoUrl: 'https://icomp.ufam.edu.br/images/nova_foto_leandro.jpg',
    email: 'galvao@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/6049960144667044',
    objetosEstudo: ['Educação em Computação', 'Mineração de Dados Educacionais', 'Ensino de Programação'],
  },
  {
    nome: 'Marco Antonio Pinheiro de Cristo',
    titulo: 'Banco de Dados e Recuperação de Informação',
    descricao: 'Doutorado - Universidade Federal de Minas Gerais',
    foto: 'MA',
    fotoUrl: 'https://icomp.ufam.edu.br/images/marco.jpg',
    email: 'marco.cristo@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/6261175351521953',
    objetosEstudo: ['Banco de Dados', 'Recuperação de Informação'],
  },
  {
    nome: 'Mário Salvatierra Júnior',
    titulo: 'Otimização, Algoritmos e Complexidade Computacional',
    descricao: 'Doutorado - Universidade Estadual de Campinas',
    foto: 'MS',
    fotoUrl: 'https://icomp.ufam.edu.br/images/mario.jpg',
    email: 'mario@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/7254679644374259',
    objetosEstudo: ['Machine Learning', 'Deep Learning', 'Inteligência Artificial', 'Pesquisa Operacional'],
  },
  {
    nome: 'Moisés Gomes de Carvalho',
    titulo: 'Banco de Dados e Recuperação de Informação',
    descricao: 'Doutorado - Universidade Federal de Minas Gerais',
    foto: 'MG',
    fotoUrl: 'https://icomp.ufam.edu.br/images/moises.jpg',
    email: 'moises@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/1840067885522796',
    objetosEstudo: ['Sistemas de Recomendação', 'Resolução de Entidades', 'Fusão de Dados', 'Mineração de Dados'],
  },
  {
    nome: 'Rafael Giusti',
    titulo: 'Aprendizado de Máquina',
    descricao: 'Doutorado - Universidade de São Paulo - ICMC',
    foto: 'RG',
    fotoUrl: 'https://icomp.ufam.edu.br/images/rafael.jpg',
    email: 'rgiusti@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/0613781010575440',
    objetosEstudo: ['Aprendizado de Máquina', 'Saúde', 'Séries Temporais', 'Reconhecimento de Padrões'],
  },
  {
    nome: 'Raimundo da Silva Barreto',
    titulo: 'Sistemas Computacionais',
    descricao: 'Doutorado - Universidade Federal de Pernambuco',
    foto: 'RS',
    fotoUrl: 'https://icomp.ufam.edu.br/images/barreto.jpg',
    email: 'barreto@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/1132672107627968',
    objetosEstudo: ['Sistemas Embarcados'],
  },
  {
    nome: 'Rosiane Freitas Rodrigues',
    titulo: 'Otimização, Algoritmos e Complexidade Computacional',
    descricao: 'Doutorado - Universidade Federal do Rio de Janeiro',
    foto: 'RF',
    fotoUrl: 'https://icomp.ufam.edu.br/images/rosiane.jpg',
    email: 'rosiane@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/8358219976594707',
    objetosEstudo: ['Teoria da Computação', 'Otimização Combinatória', 'Pesquisa Operacional'],
  },
  {
    nome: 'Ruiter Braga Caldas',
    titulo: 'Sistemas Embarcados',
    descricao: 'Doutorado - Universidade Federal de Minas Gerais',
    foto: 'RB',
    fotoUrl: 'https://icomp.ufam.edu.br/images/ruiter.jpg',
    email: 'ruiter@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/9686087091192989',
    objetosEstudo: ['Sistemas Embarcados'],
  },
  {
    nome: 'Tanara Lauschner',
    titulo: 'Inteligência Artificial',
    descricao: 'Doutorado - Pontifícia Universidade Católica do Rio de Janeiro',
    foto: 'TL',
    fotoUrl: 'https://icomp.ufam.edu.br/images/tanara.jpg',
    email: 'tanara@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/7433400746822554',
    objetosEstudo: ['Inteligência Artificial'],
  },
  {
    nome: 'Tayana Uchoa Conte',
    titulo: 'Engenharia de Software',
    descricao: 'Doutorado - Universidade Federal do Rio de Janeiro',
    foto: 'TU',
    fotoUrl: 'https://icomp.ufam.edu.br/images/tayana.jpg',
    email: 'tayana@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/6682919653508224',
    objetosEstudo: ['Engenharia de Software', 'Interação Humano-Computador', 'UX'],
  },
  {
    nome: 'Thais Helena Chaves de Castro',
    titulo: 'Inteligência Artificial',
    descricao: 'Doutorado - Pontifícia Universidade Católica do Rio de Janeiro',
    foto: 'TH',
    fotoUrl: 'https://icomp.ufam.edu.br/images/thais.jpg',
    email: 'thais@icomp.ufam.edu.br',
    lattes: 'http://lattes.cnpq.br/9337143918677200',
    objetosEstudo: ['Inclusão', 'Acessibilidade', 'Inteligência Artificial'],
  },
];

@Component({
  selector: 'app-buscar-tcc',
  templateUrl: './buscar-tcc.component.html',
  styleUrls: ['./buscar-tcc.component.css'],
})
export class BuscarTccComponent {
  readonly professores = ICOMP_PROFESSORES;

  readonly form = this.fb.nonNullable.group({
    titulo: [''],
    aluno: [''],
    area_tematica: [''],
    curso: [''],
  });

  isLoading = false;
  errorMessage = '';
  resultados: TccPublico[] = [];
  buscaRealizada = false;
  readonly isAuthenticated: boolean;
  readonly painelRoute: string[];

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly publicoService: PublicoService,
    private readonly router: Router,
  ) {
    this.isAuthenticated = this.authService.isAuthenticated();
    this.painelRoute = this.authService.getPostLoginRoute();
  }

  buscar(): void {
    if (this.isLoading) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.buscaRealizada = false;

    this.publicoService.buscarTcc(this.buildParams())
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (resultados) => {
          this.resultados = resultados;
          this.buscaRealizada = true;
        },
        error: (error: unknown) => {
          this.errorMessage = getApiErrorMessage(error, 'Não foi possível realizar a busca.');
        },
      });
  }

  verDetalhe(id: string): void {
    void this.router.navigate(['/consultor-externo', id]);
  }

  private buildParams(): BuscarTccParams {
    const values = this.form.getRawValue();
    return {
      ...(values.titulo.trim() ? { titulo: values.titulo.trim() } : {}),
      ...(values.aluno.trim() ? { aluno: values.aluno.trim() } : {}),
      ...(values.area_tematica.trim() ? { area_tematica: values.area_tematica.trim() } : {}),
      ...(values.curso.trim() ? { curso: values.curso.trim() } : {}),
    };
  }
}
