# Limits made consistent across the app:
# - Produto.preco: at least 0.01 (no free or negative products) and no default of 0, so a product
#   can't be saved without a price. The maximum stays 999.99.
# - Addresses (Perfil.morada, Checkout.morada): 150 characters. The old 50 was never enforced and
#   is shorter than real addresses. TextField lengths are checked by forms, not by the database,
#   so this changes no table.
import django.core.validators
from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitepizza', '0030_valorpedido_decimal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produto',
            name='preco',
            field=models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]),
        ),
        migrations.AlterField(
            model_name='perfil',
            name='morada',
            field=models.TextField(max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='checkout',
            name='morada',
            field=models.TextField(max_length=150, null=True),
        ),
    ]
