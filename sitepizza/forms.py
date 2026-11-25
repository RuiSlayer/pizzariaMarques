from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import re

from .models import MORADA_MAX, Perfil


def _texto(placeholder, autocomplete, tipo=forms.TextInput):
    return tipo(attrs={"placeholder": placeholder, "class": "form-control", "autocomplete": autocomplete})


class CreateUserForm(UserCreationForm):
    username = forms.CharField(label=_("Nome de utilizador"), widget=_texto(_("ex.: joao.silva"), "username"))
    email = forms.EmailField(label=_("Email"), widget=_texto(_("nome@exemplo.pt"), "email", forms.EmailInput))
    password1 = forms.CharField(label=_("Palavra-passe"), widget=_texto(_("Escolhe uma palavra-passe"), "new-password", forms.PasswordInput))
    password2 = forms.CharField(label=_("Confirmar palavra-passe"), widget=_texto(_("Repete a palavra-passe"), "new-password", forms.PasswordInput))

    class Meta:
        model = User
        fields = ['username', 'email']


class PerfilForm(ModelForm):
    morada = forms.CharField(label=_("Morada"), max_length=MORADA_MAX,   # also sets the input's maxlength
                             widget=_texto(_("Ex.: Rua da Rosa n.º 2, 1.º Esq."), "street-address"))
    telemovel = forms.CharField(label=_("Telemóvel"), max_length=20,
                                widget=_texto("9xx xxx xxx", "tel", forms.TextInput))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['telemovel'].widget.input_type = 'tel'        # phone keypad on mobiles

    def clean_telemovel(self):
        """A Portuguese number as people type it: '912 345 678', '912-345-678', '+351 912 345 678'.

        Stored as the 9 digits (the model field is an integer), mobile (9x) or landline (2x).
        """
        numero = re.sub(r'[\s.\-()]', '', self.cleaned_data['telemovel'])
        numero = re.sub(r'^(\+|00)351', '', numero)
        if not re.fullmatch(r'[29]\d{8}', numero):
            raise forms.ValidationError(_('Indica um número português com 9 dígitos, por exemplo 912 345 678.'))
        return int(numero)

    class Meta:
        model = Perfil
        fields = ['morada', 'telemovel']
