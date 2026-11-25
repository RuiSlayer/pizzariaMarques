# Order totals are money: store them as Decimal with 2 places, like Produto.preco.
# As a float, 26.00 was saved as 26.0 and the confirmation page showed "26,0 €".

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitepizza', '0029_catalogo_inicial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedido',
            name='valorPedido',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
    ]
