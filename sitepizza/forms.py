from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import Perfil


def _texto(placeholder, autocomplete, tipo=forms.TextInput):
    return tipo(attrs={"placeholder": placeholder, "class": "form-control", "autocomplete": autocomplete})


class CreateUserForm(UserCreationForm):
    username = forms.CharField(label="Nome de utilizador", widget=_texto("ex.: joao.silva", "username"))
    email = forms.EmailField(label="Email", widget=_texto("nome@exemplo.pt", "email", forms.EmailInput))
    password1 = forms.CharField(label="Palavra-passe", widget=_texto("Escolhe uma palavra-passe", "new-password", forms.PasswordInput))
    password2 = forms.CharField(label="Confirmar palavra-passe", widget=_texto("Repete a palavra-passe", "new-password", forms.PasswordInput))

    class Meta:
        model = User
        fields = ['username', 'email']


class PerfilForm(ModelForm):
    morada = forms.CharField(label="Morada", widget=_texto("Ex.: Rua da Rosa n.º 2, 1.º Esq.", "street-address"))
    telemovel = forms.CharField(label="Telemóvel", widget=_texto("9xx xxx xxx", "tel", forms.TextInput))

    class Meta:
        model = Perfil
        fields = ['morada', 'telemovel']
