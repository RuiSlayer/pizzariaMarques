from django.apps import AppConfig


class SitepizzaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sitepizza'

    def ready(self):
        # Keep the storage bucket in sync with the database:
        #  - a new image gets its responsive sizes,
        #  - a replaced or deleted image has its whole directory removed (no orphaned files).
        from django.db.models.signals import post_delete, post_save, pre_save
        from .imagens import apagar_grupo, gerar_variantes
        from .models import Perfil, Produto

        def _guardar_anterior(sender, instance, **kwargs):
            anterior = sender.objects.filter(pk=instance.pk).values_list('image', flat=True).first() if instance.pk else None
            instance._imagem_anterior = anterior or ''

        def _depois_de_guardar(sender, instance, **kwargs):
            atual = instance.image.name if instance.image else ''
            anterior = getattr(instance, '_imagem_anterior', '')
            if anterior and anterior != atual:
                apagar_grupo(anterior)
            if atual:
                gerar_variantes(atual)

        def _depois_de_apagar(sender, instance, **kwargs):
            if instance.image:
                apagar_grupo(instance.image.name)

        # weak=False: signals only keep a weak reference by default, and these handlers are local
        # functions that nothing else refers to, so they would be dropped as soon as ready() returns.
        for modelo in (Produto, Perfil):
            pre_save.connect(_guardar_anterior, sender=modelo, weak=False, dispatch_uid=f'anterior_{modelo.__name__}')
            post_save.connect(_depois_de_guardar, sender=modelo, weak=False, dispatch_uid=f'variantes_{modelo.__name__}')
            post_delete.connect(_depois_de_apagar, sender=modelo, weak=False, dispatch_uid=f'apagar_{modelo.__name__}')
