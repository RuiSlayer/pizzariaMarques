"""Point the menu products at the new photo set in media/produtos/.

Photos are free-licence images from Pexels (no attribution required), cropped
to 4:3 and colour-graded to match; see media/produtos/CREDITOS.txt.
"""
from django.db import migrations

IMAGENS = {
    "Dom Manuel": "dom-manuel",
    "Dom Pedro": "dom-pedro",
    "Dom Sancho": "dom-sancho",
    "Dom Dinis": "dom-dinis",
    "Dom Sebastião": "dom-sebastiao",
    "Dom Afonso": "dom-afonso",
    "Dom Henrrique": "dom-henrique",
    "Dom Henrique": "dom-henrique",
    "Dom João": "dom-joao",
    "Pão de Alho": "pao-de-alho",
    "Asas de Frango": "asas-de-frango",
    "Nuggets": "nuggets",
    "Mousse": "mousse",
    "Crepe de Chocolate": "crepe-chocolate",
    "Gelado": "gelado",
    "Waffle": "waffle",
    "Água 1,5L": "agua",
    "Coca-Cola 1,5L": "coca-cola",
    "Ice Tea 1,5L": "ice-tea",
    "Sumol 1,5L": "sumol",
}


def aplicar(apps, schema_editor):
    Produto = apps.get_model("sitepizza", "Produto")
    for nome, slug in IMAGENS.items():
        Produto.objects.filter(nome=nome).update(image=f"media/produtos/{slug}.jpg")


class Migration(migrations.Migration):
    dependencies = [("sitepizza", "0026_auto_20210430_2355")]
    operations = [migrations.RunPython(aplicar, migrations.RunPython.noop)]
