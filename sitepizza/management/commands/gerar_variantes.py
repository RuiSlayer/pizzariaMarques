from django.core.management.base import BaseCommand

from sitepizza.imagens import gerar_variantes
from sitepizza.models import Perfil, Produto


class Command(BaseCommand):
    help = "Gera as versões redimensionadas (WebP + JPEG) das imagens de produtos e perfis."

    def add_arguments(self, parser):
        parser.add_argument("--forcar", action="store_true", help="Regenerar mesmo as que já existem.")

    def handle(self, *args, forcar=False, **options):
        total = 0
        for modelo in (Produto, Perfil):
            for obj in modelo.objects.exclude(image=""):
                n = gerar_variantes(obj.image.name, forcar=forcar)
                total += n
                if n:
                    self.stdout.write(f"{modelo.__name__} {obj.pk}: {obj.image.name} ({n} ficheiros)")
        self.stdout.write(self.style.SUCCESS(f"{total} ficheiros gerados."))
