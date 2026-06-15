import random
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstração para a Boss Barbearia'

    def handle(self, *args, **kwargs):
        from barbearia.models import (Agendamento, Cliente, Notificacao,
                                       PerfilUsuario, Saida, Servico)

        self.stdout.write(self.style.MIGRATE_HEADING('Populando Boss Barbearia...'))

        # Admin
        admin, _ = User.objects.get_or_create(username='boss_admin', defaults={
            'first_name': 'Carlos', 'last_name': 'Silva', 'email': 'admin@bossbarbearia.com',
            'is_staff': True, 'is_superuser': True,
        })
        admin.set_password('admin123')
        admin.save()
        PerfilUsuario.objects.get_or_create(usuario=admin, defaults={'cargo': 'admin', 'telefone': '83999990001'})

        # Barbeiros
        barbeiros_raw = [
            ('rafael_boss', 'Rafael', 'Santos', '83999990002'),
            ('marcos_boss', 'Marcos', 'Oliveira', '83999990003'),
            ('thiago_boss', 'Thiago', 'Pereira', '83999990004'),
        ]
        barbeiros = []
        for uname, first, last, tel in barbeiros_raw:
            u, _ = User.objects.get_or_create(username=uname, defaults={'first_name': first, 'last_name': last})
            u.set_password('boss123')
            u.save()
            PerfilUsuario.objects.get_or_create(usuario=u, defaults={'cargo': 'barbeiro', 'telefone': tel})
            barbeiros.append(u)

        # Serviços
        servicos_raw = [
            ('Corte Tradicional', 'Corte clássico com tesoura e máquina', 35.00, 30),
            ('Corte + Barba', 'Combo completo: corte e barba modelada', 55.00, 50),
            ('Barba Completa', 'Modelagem, hidratação e finalização de barba', 25.00, 25),
            ('Pezinho', 'Acabamento fino no pescoço', 15.00, 15),
            ('Platinado', 'Descoloração e platinado completo', 120.00, 90),
            ('Sobrancelha', 'Design e modelagem de sobrancelha', 15.00, 15),
            ('Pigmentação', 'Pigmentação de barba ou cabelo', 80.00, 60),
        ]
        servicos = []
        for nome, desc, preco, dur in servicos_raw:
            s, _ = Servico.objects.get_or_create(nome=nome, defaults={'descricao': desc, 'preco': preco, 'duracao_minutos': dur})
            servicos.append(s)

        # Clientes
        clientes_raw = [
            ('João Pedro Alves', '83999880001'), ('Lucas Mendonça', '83999880002'),
            ('Gabriel Costa', '83999880003'), ('Pedro Henrique Silva', '83999880004'),
            ('Mateus Ferreira', '83999880005'), ('Bruno Carvalho', '83999880006'),
            ('Diego Martins', '83999880007'), ('Felipe Rodrigues', '83999880008'),
            ('Anderson Lima', '83999880009'), ('Ricardo Sousa', '83999880010'),
            ('Thiago Araújo', '83999880011'), ('Leonardo Nunes', '83999880012'),
            ('Eduardo Campos', '83999880013'), ('Gustavo Barbosa', '83999880014'),
            ('Henrique Dias', '83999880015'),
        ]
        clientes = []
        for nome, tel in clientes_raw:
            c, _ = Cliente.objects.get_or_create(nome=nome, defaults={'telefone': tel})
            clientes.append(c)

        # Agendamentos — últimos 30 dias + próximos 7
        hoje = date.today()
        horarios = [9, 10, 11, 13, 14, 15, 16, 17]
        status_passado = ['concluido'] * 5 + ['faltou', 'cancelado']

        created = 0
        for delta in range(-30, 8):
            d = hoje + timedelta(days=delta)
            for _ in range(random.randint(4, 9)):
                barb = random.choice(barbeiros)
                cli = random.choice(clientes)
                svc = random.choice(servicos)
                hora = random.choice(horarios)
                dt = timezone.make_aware(
                    timezone.datetime(d.year, d.month, d.day, hora, random.choice([0, 30]))
                )
                if delta < 0:
                    status = random.choice(status_passado)
                elif delta == 0:
                    status = random.choice(['agendado', 'confirmado', 'concluido'])
                else:
                    status = 'agendado'

                ag, new = Agendamento.objects.get_or_create(
                    cliente=cli, barbeiro=barb, data_hora=dt,
                    defaults={'servico': svc, 'status': status, 'valor_cobrado': svc.preco},
                )
                if new:
                    created += 1

        # Despesas do mês atual
        despesas = [
            ('Aluguel do Espaço', 2500.00, 'aluguel'),
            ('Produtos (Shampoo, Condicionador)', 420.00, 'produtos'),
            ('Giletes e Lâminas', 85.00, 'produtos'),
            ('Conta de Luz', 280.00, 'outros'),
            ('Internet', 89.90, 'outros'),
            ('Manutenção Cadeira de Barbeiro', 150.00, 'equipamentos'),
            ('Salário Recepcionista', 1400.00, 'salario'),
        ]
        for desc, valor, cat in despesas:
            dia = random.randint(1, min(hoje.day, 28))
            Saida.objects.get_or_create(
                descricao=desc, data=date(hoje.year, hoje.month, dia),
                defaults={'valor': valor, 'categoria': cat, 'registrado_por': admin},
            )

        # Notificações para cada barbeiro
        for barb in barbeiros:
            Notificacao.objects.get_or_create(
                usuario=barb,
                mensagem='Bem-vindo ao Boss Barbearia! Você tem agendamentos para hoje.',
                defaults={'tipo': 'aviso', 'lida': False},
            )

        self.stdout.write(self.style.SUCCESS(f'\n✓ Boss Barbearia populada! {created} agendamentos criados.\n'))
        self.stdout.write('  Credenciais de acesso:')
        self.stdout.write('  Admin     → boss_admin / admin123')
        self.stdout.write('  Barbeiros → rafael_boss, marcos_boss, thiago_boss / boss123\n')
