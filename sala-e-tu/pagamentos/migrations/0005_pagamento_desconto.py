from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pagamentos', '0004_bancopix_pagamento_data_banco'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagamento',
            name='desconto',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Desconto (R$)'),
        ),
    ]
