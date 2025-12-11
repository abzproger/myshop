from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _


class RussianAuthenticationForm(AuthenticationForm):
    """
    Форма аутентификации с русскими сообщениями об ошибках.
    """

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _(
            "Пожалуйста, введите правильные имя пользователя и пароль. "
            "Оба поля могут зависеть от регистра."
        ),
        "inactive": _("Этот аккаунт отключен."),
    }


User = get_user_model()


class RussianUserCreationForm(UserCreationForm):
    """
    Форма регистрации с русскими подсказками и подписями к полям пароля.
    """

    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
            }
        ),
        help_text=(
            "Пароль не должен быть слишком похож на другую вашу личную информацию.<br>"
            "Пароль должен содержать как минимум 8 символов.<br>"
            "Пароль не должен быть слишком простым и распространённым.<br>"
            "Пароль не может состоять только из цифр."
        ),
    )

    password2 = forms.CharField(
        label="Подтверждение пароля",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
            }
        ),
        help_text="Введите тот же пароль ещё раз для проверки.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)
        help_texts = {
            "username": _(
                "Обязательное поле. Не более 150 символов. "
                "Допустимы буквы, цифры и символы @/./+/-/_."
            ),
        }

