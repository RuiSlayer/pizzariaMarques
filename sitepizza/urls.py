from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'navegar'
urlpatterns = [
 path("", views.home, name="home"),
 path("home", views.home, name="home"),
 path("menu", views.menu, name="menu"),
 path("perfil/<int:user_id>", views.perfil, name="perfil"),
 path("sobrenos", views.sobrenos, name="sobrenos"),
 path("contactos", views.contactos, name="contactos"),
 path("menu/checkout", views.checkout, name="checkout"),
 path("registo", views.registo, name="registo"),
 path("login", views.loginPage, name="login"),
 path("logout", views.logoutUser, name="logout"),
 path("add_carrinho", views.add_carrinho, name="add_carrinho"),
 path("alterar_carrinho", views.alterar_carrinho, name="alterar_carrinho"),
 path("checkout/finalizar", views.finalizar, name="finalizar"),
 path('finalizar/<int:checkout_id>/', views.finalizar_confirmacao, name='finalizar_confirmacao'),
 path('fazer_upload', views.fazer_upload, name='fazer_upload'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Uploads (product photos, avatars) in production-like runs. Django never overwrites an upload
    # (a new file gets a new name), so a one-year max-age is safe.
    from django.urls import re_path
    from django.views.decorators.cache import cache_control
    from django.views.static import serve
    urlpatterns += [
        re_path(r'^' + settings.MEDIA_URL.lstrip('/') + r'(?P<path>.*)$',
                cache_control(max_age=31536000, public=True)(serve),
                {'document_root': settings.MEDIA_ROOT}),
    ]