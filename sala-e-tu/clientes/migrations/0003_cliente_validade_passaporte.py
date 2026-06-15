from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0002_remove_cliente_documento_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='validade_passaporte',
            field=models.DateField(blank=True, null=True, verbose_name='Validade do Passaporte'),
        ),
    ]
