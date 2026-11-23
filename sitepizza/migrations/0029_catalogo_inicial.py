"""Seed the menu on a fresh database.

The catalogue used to exist only inside the committed db.sqlite3. Now that the database is no
longer in the repository, a new install (e.g. the Postgres container) would start with an empty
menu, so the categories and products are created here. The photos are in storage/produtos/.

Does nothing when the database already has categories or products.
"""
from decimal import Decimal

from django.db import migrations

# The menu view finds each section by category name (categoria__nome__icontains).
CATALOGO = {
    "pizza": [
        ("Dom Manuel", "Ingredientes: Molho de Tomate, Mozzarella, Extra Queijo, Pepperoni, Pimentos", "13", "dom-manuel"),
        ("Dom Pedro", "Ingredientes: Molho de Tomate, Mozzarella, Frango, Queijo Catupiry, Milho, Ananás", "14", "dom-pedro"),
        ("Dom Sancho", "Ingredientes: Molho de Tomate, Mozzarela, Bacon, Azeitonas Pretas, Extra queijo, Cogumelos", "13", "dom-sancho"),
        ("Dom Dinis", "Ingredientes: Molho de Tomate, Mozzarela, Cabra, Extra Mozzarela, Provolore, e Parmesão", "13", "dom-dinis"),
        ("Dom Sebastião", "Ingredientes: Molho Barbecue, Mozzarela, Calabresa, Cebola, extra queijo", "14", "dom-sebastiao"),
        ("Dom Afonso", "Ingredientes: Molho de Tomate, Mozzarella, Atum, Cebola, Tomate, Milho", "13", "dom-afonso"),
        ("Dom Henrique", "Ingredientes: Molho de Tomate, Mozzarela, Bacon, Carne Picada, Azeitonas, Cebola", "13", "dom-henrique"),
        ("Dom João", "Ingredientes: Molho de Tomate, Mozzarela, Cogumelos, Azeitonas, Ovo, Milho", "13", "dom-joao"),
    ],
    "acompanhamento": [
        ("Pão de Alho", "Quentinho", "5", "pao-de-alho"),
        ("Asas de Frango", "", "5", "asas-de-frango"),
        ("Nuggets", "", "3", "nuggets"),
    ],
    "bebida": [
        ("Água 1,5L", "", "1.5", "agua"),
        ("Coca-Cola 1,5L", "", "2.5", "coca-cola"),
        ("Ice Tea 1,5L", "", "2.5", "ice-tea"),
        ("Sumol 1,5L", "", "2.5", "sumol"),
    ],
    "sobremesa": [
        ("Mousse", "", "3", "mousse"),
        ("Crepe de Chocolate", "Crepe de Chocolate", "3", "crepe-chocolate"),
        ("Gelado", "", "3", "gelado"),
        ("Waffle", "", "3", "waffle"),
    ],
}


def semear(apps, schema_editor):
    Categoria = apps.get_model("sitepizza", "Categoria")
    Produto = apps.get_model("sitepizza", "Produto")
    if Categoria.objects.exists() or Produto.objects.exists():
        return
    for nome_categoria, produtos in CATALOGO.items():
        categoria = Categoria.objects.create(nome=nome_categoria)
        for nome, descricao, preco, pasta in produtos:
            Produto.objects.create(
                nome=nome,
                descricao=descricao,
                preco=Decimal(preco),
                categoria=categoria,
                image=f"produtos/{pasta}/original.jpg",
            )


class Migration(migrations.Migration):
    dependencies = [("sitepizza", "0028_storage_bucket")]
    operations = [migrations.RunPython(semear, migrations.RunPython.noop)]
