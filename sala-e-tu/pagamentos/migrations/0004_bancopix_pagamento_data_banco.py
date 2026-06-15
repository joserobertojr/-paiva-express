import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pagamentos', '0003_pagamento_parcelas_pagamento_vendedor'),
    ]

    operations = [
        migrations.CreateModel(
            name='BancoPix',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome do Banco')),
                ('ativo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Banco PIX',
                'verbose_name_plural': 'Bancos PIX',
                'ordering': ['nome'],
            },
        ),
        migrations.AddField(
            model_name='pagamento',
            name='data_pagamento',
            field=models.DateField(default=datetime.date.today, verbose_name='Data do Pagamento'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pagamento',
            name='banco_pix',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pagamentos',
                to='pagamentos.bancopix',
                verbose_name='Banco PIX',
            ),
        ),
    ]
