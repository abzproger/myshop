import re

from django import forms
from django.core.exceptions import ValidationError


class CheckoutContactForm(forms.Form):
    """Шаг 1: контактные данные покупателя."""

    full_name = forms.CharField(
        label="ФИО",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Иванов Иван Иванович",
            }
        ),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "you@example.com",
            }
        ),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=32,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "+7 (999) 123-45-67",
            }
        ),
    )

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        normalized = re.sub(r"[^\d+]", "", phone)

        # Допускаем: +7XXXXXXXXXX, 8XXXXXXXXXX, 7XXXXXXXXXX (приведём к +7...)
        if normalized.startswith("+7") and len(normalized) == 12:
            return normalized
        if normalized.startswith("8") and len(normalized) == 11:
            return "+7" + normalized[1:]
        if normalized.startswith("7") and len(normalized) == 11:
            return "+7" + normalized[1:]

        raise ValidationError("Укажите телефон в формате +7XXXXXXXXXX")


class CheckoutAddressForm(forms.Form):
    """Шаг 2: адрес и способ получения."""

    DELIVERY_CHOICES = [
        ("courier", "Доставка курьером"),
        ("pickup", "Самовывоз"),
    ]

    delivery_method = forms.ChoiceField(
        label="Способ получения",
        choices=DELIVERY_CHOICES,
        widget=forms.RadioSelect,
    )

    city = forms.CharField(
        label="Город",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Москва",
            }
        ),
    )
    address_line = forms.CharField(
        label="Адрес доставки",
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "ул. Примерная, д. 1, кв. 1",
            }
        ),
    )
    postal_code = forms.CharField(
        label="Почтовый индекс",
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "101000",
            }
        ),
    )
    comment = forms.CharField(
        label="Комментарий к заказу",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Например: позвонить заранее, подъезд 3, код 1234",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        delivery_method = cleaned_data.get("delivery_method")

        # Для курьерской доставки город и адрес обязательны
        if delivery_method == "courier":
            if not cleaned_data.get("city"):
                self.add_error("city", "Укажите город для доставки курьером.")
            if not cleaned_data.get("address_line"):
                self.add_error("address_line", "Укажите адрес для доставки курьером.")

        # Для самовывоза адресные поля могут быть пустыми
        return cleaned_data


class OrderCancelForm(forms.Form):
    reason = forms.ChoiceField(
        label="Причина отмены",
        choices=(),
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].choices = self._get_reason_choices()

    @staticmethod
    def _get_reason_choices():
        from .models import Order

        return Order.CANCEL_REASON_CHOICES


