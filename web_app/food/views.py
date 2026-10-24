from django.shortcuts import render, redirect

from core.views import _require_login


def home(request):
    if not _require_login(request):
        return redirect("login")
    return render(request, "food/home.html")
