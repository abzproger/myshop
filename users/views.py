from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import RussianUserCreationForm


def signup(request):
    """Регистрация нового пользователя."""
    if request.user.is_authenticated:
        return redirect("catalog:index")

    if request.method == "POST":
        form = RussianUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно, вы вошли в систему.")
            return redirect("catalog:index")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме регистрации.")
    else:
        form = RussianUserCreationForm()

    return render(request, "users/signup.html", {"form": form})


@login_required
def profile(request):
    """Страница профиля пользователя."""
    return render(request, "users/profile.html")
