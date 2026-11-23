"""Move uploads out of the app's static folder into the storage bucket (MEDIA_ROOT = storage/).

Before: sitepizza/static/media/media/produtos/dom-manuel.jpg (+ dom-manuel-320.webp, ...)
After:  storage/produtos/dom-manuel/original.jpg            (+ 320.webp, ... in the same folder)

Profile photos whose file no longer exists are cleared, so no page links to a missing image.
"""
import os
import re
import shutil

from django.conf import settings
from django.db import migrations, models
from django.utils.text import slugify

import sitepizza.models

LEGADO = os.path.join(settings.BASE_DIR, "sitepizza", "static", "media")


def _mover(apps, schema_editor):
    for modelo, pasta in (("Produto", "produtos"), ("Perfil", "avatars")):
        Modelo = apps.get_model("sitepizza", modelo)
        for obj in Modelo.objects.exclude(image="").exclude(image__isnull=True):
            nome = obj.image.name
            stem, ext = os.path.splitext(os.path.basename(nome))
            if stem == "original":
                continue  # already in the new layout
            novo = f"{pasta}/{slugify(stem) or 'imagem'}/original{ext.lower()}"
            antigo = os.path.join(LEGADO, nome)
            destino = os.path.join(settings.MEDIA_ROOT, novo)
            if os.path.exists(antigo):
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                pasta_antiga = os.path.dirname(antigo)
                for f in os.listdir(pasta_antiga):
                    m = re.fullmatch(re.escape(stem) + r"-(\d+)\.(avif|webp|jpg)", f)
                    if m:
                        shutil.move(os.path.join(pasta_antiga, f), os.path.join(os.path.dirname(destino), f"{m[1]}.{m[2]}"))
                shutil.move(antigo, destino)
            if os.path.exists(destino) or modelo == "Produto":
                Modelo.objects.filter(pk=obj.pk).update(image=novo)
            else:
                Modelo.objects.filter(pk=obj.pk).update(image="")


class Migration(migrations.Migration):
    dependencies = [("sitepizza", "0027_imagens_produtos")]

    operations = [
        migrations.AlterField(
            model_name="perfil",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to=sitepizza.models.caminho_avatar),
        ),
        migrations.AlterField(
            model_name="produto",
            name="image",
            field=models.ImageField(upload_to=sitepizza.models.caminho_produto),
        ),
        migrations.RunPython(_mover, migrations.RunPython.noop),
    ]
