from django import forms
from django.core.exceptions import ValidationError
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    consent = forms.BooleanField(
        required=True,
        label="Я согласен на обработку персональных данных",
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'id': 'email',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'phone',
                'placeholder': '+7 (999) 123-45-67',
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select',
                'id': 'subject',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'message',
                'rows': 5,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Локализованные подписи и плейсхолдеры
        self.fields['name'].label = "Ваше имя"
        self.fields['email'].label = "Email"
        self.fields['phone'].label = "Телефон"
        self.fields['subject'].label = "Тема обращения"
        self.fields['subject'].required = False
        self.fields['subject'].empty_label = "Выберите тему"
        self.fields['message'].label = "Сообщение"
        self.fields['consent'].widget.attrs.update({'class': 'form-check-input', 'id': 'consent'})

    def clean_message(self):
        message = self.cleaned_data.get('message', '')
        if len(message) > 5000:
            raise ValidationError("Сообщение не должно превышать 5000 символов.")
        return message







