import json

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.utils import timezone
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User

from .models import *
from .forms import *

__all__ = [
    "IndexView",
    "JoinView",
    "SignInView",
    "SignOutView",
    "AddArtView",
    "UserListView",
    "UserView",
    "ArtGalleryView",
]


class IndexView(ListView):
    template_name = "core/index.html"
    context_object_name = "arts"
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
          following = user.following.all()

          return (
              Art.objects
              .filter(artist__in=following)
              .order_by("-timestamp")
          )

        else:
            return []


class JoinView(CreateView):
    template_name = "core/join.html"
    form_class = JoinForm
    success_url = reverse_lazy("core:index")


class SignInView(LoginView):
    template_name = "core/sign_in.html"


class SignOutView(LogoutView):
    pass


class AddArtView(LoginRequiredMixin, CreateView):
    template_name = "core/add.html"
    form_class = ArtForm
    success_url = reverse_lazy("core:index")

    def form_valid(self, form):
        form.instance.artist = self.request.user

        return super().form_valid(form)


class UserListView(ListView):
    template_name = "core/users.html"
    context_object_name = "users"
    paginate_by = 100

    def get_queryset(self):
        return (
              User.objects
              .order_by("username")
        )


class UserView(DetailView):
    template_name = "core/user.html"
    context_object_name = "user"

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs["username"])

    def post(self, request, username):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            follow_user = json.load(request)["follow_user"]

            follower = request.user
            target = self.get_object()
            if follow_user:
                follower.following.add(target)
            else:
                follower.following.remove(target)

            user_followed = target in follower.following.all()

            return JsonResponse({"user_followed": user_followed})

        else:
            return super().post(request, username)

class ArtGalleryView(ListView):
    template_name = "core/arts.html"
    context_object_name = "arts"
    paginate_by = 25

    def get_queryset(self):
        return (
            Art.objects
            .order_by("-timestamp")
        )
