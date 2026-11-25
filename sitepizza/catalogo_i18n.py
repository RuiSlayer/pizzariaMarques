"""Translatable texts that live in the database rather than in the code.

Product names and descriptions (seeded by migrations/0029_catalogo_inicial.py) and the delivery /
payment choices stored on a Checkout are Portuguese data. They are shown through the
{{ texto|traduzir }} filter (templatetags/traducoes.py), which looks them up in the translation
catalogue; this module only lists them so `makemessages` adds them to the .po files. A text with
no entry (a product added later in the admin, a typed address) is shown as it is.
"""
from django.utils.translation import gettext_noop as _

TEXTOS = [
    # Products: names
    _("Pão de Alho"),
    _("Asas de Frango"),
    _("Nuggets"),
    _("Água 1,5L"),
    _("Coca-Cola 1,5L"),
    _("Ice Tea 1,5L"),
    _("Sumol 1,5L"),
    _("Mousse"),
    _("Crepe de Chocolate"),
    _("Gelado"),
    _("Waffle"),
    # Products: descriptions (exactly as stored)
    _("Ingredientes: Molho de Tomate, Mozzarella, Extra Queijo, Pepperoni, Pimentos"),
    _("Ingredientes: Molho de Tomate, Mozzarella, Frango, Queijo Catupiry, Milho, Ananás"),
    _("Ingredientes: Molho de Tomate, Mozzarela, Bacon, Azeitonas Pretas, Extra queijo, Cogumelos"),
    _("Ingredientes: Molho de Tomate, Mozzarela, Cabra, Extra Mozzarela, Provolore, e Parmesão"),
    _("Ingredientes: Molho Barbecue, Mozzarela, Calabresa, Cebola, extra queijo"),
    _("Ingredientes: Molho de Tomate, Mozzarella, Atum, Cebola, Tomate, Milho"),
    _("Ingredientes: Molho de Tomate, Mozzarela, Bacon, Carne Picada, Azeitonas, Cebola"),
    _("Ingredientes: Molho de Tomate, Mozzarela, Cogumelos, Azeitonas, Ovo, Milho"),
    _("Quentinho"),
    # Checkout: stored payment values (the delivery values are the checkout labels)
    _("Dinheiro"),
    _("Cartao"),
    _("Mbway"),
]
