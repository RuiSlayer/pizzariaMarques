"""Language selection.

Django's LocaleMiddleware would also pick the language from the browser's Accept-Language header.
This is a Portuguese neighbourhood shop, so the site stays in Portuguese unless the visitor
chooses English with the PT / EN switch (Django's set_language view, which stores the choice in
the language cookie). A plain middleware keeps that rule explicit.
"""
from django.conf import settings
from django.utils import translation
from django.utils.cache import patch_vary_headers


class IdiomaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.codigos = {codigo for codigo, _ in settings.LANGUAGES}

    def __call__(self, request):
        codigo = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if codigo not in self.codigos:
            codigo = settings.LANGUAGE_CODE
        translation.activate(codigo)
        request.LANGUAGE_CODE = codigo

        response = self.get_response(request)

        # The same URL serves either language, depending on the cookie.
        patch_vary_headers(response, ('Cookie',))
        response.headers.setdefault('Content-Language', codigo)
        translation.deactivate()
        return response
