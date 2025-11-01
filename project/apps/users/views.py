from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            messages.error(request, "Пароли не совпадают.")
            return redirect("users:register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Имя пользователя уже занято.")
            return redirect("users:register")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect("shop:products")

    return render(request, "users/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("shop:products")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
            return redirect("users:login")

    return render(request, "users/login.html")


def logout_view(request):
    logout(request)
    return redirect("users:login")


@login_required
def profile_view(request):
    return render(request, "users/profile.html", {"user": request.user})


@login_required
def profile_update(request):
    if request.method == "POST":
        user = request.user
        username = request.POST.get("username")
        email = request.POST.get("email")
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        new_password2 = request.POST.get("new_password2")

        if username and username != user.username:
            if user.__class__.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, "Имя пользователя уже занято.")
                return redirect("users:profile")
            user.username = username

        if email and email != user.email:
            if user.__class__.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, "Email уже используется.")
                return redirect("users:profile")
            user.email = email

        if new_password or new_password2:
            if not current_password:
                messages.error(request, "Введите текущий пароль для смены пароля.")
                return redirect("users:profile")
            if not user.check_password(current_password):
                messages.error(request, "Текущий пароль неверный.")
                return redirect("users:profile")
            if new_password != new_password2:
                messages.error(request, "Новые пароли не совпадают.")
                return redirect("users:profile")
            user.set_password(new_password)
            update_session_auth_hash(request, user)

        user.save()
        messages.success(request, "Данные профиля успешно обновлены.")
        return redirect("users:profile")

    return redirect("users:profile")