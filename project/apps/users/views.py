from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
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
