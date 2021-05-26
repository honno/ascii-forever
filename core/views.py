import json

from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.views.generic.base import TemplateView, ContextMixin
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import MultipleObjectMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.utils.html import linebreaks
from django.core.exceptions import ValidationError
from werkzeug.wsgi import FileWrapper


from .models import *
from .forms import *

__all__ = [
    "IndexView",

    "JoinView",
    "SignInView",
    "SignOutView",

    "UserListView",
    "UserView",
    "SettingsView",

    "ArtGalleryView",
    "ArtView",
    "art_thumb",
    "PostArtView",
    "ArtEditView",

    "edit_comment",
    "follow_user",
    "like_art",
    "nsfw_pref",
]


# ------------------------------------------------------------------------------
# Home page


class IndexView(ListView):
    template_name = "core/pages/index.html"
    context_object_name = "arts"
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            following = user.following.all()

            arts = Art.objects.filter(artist__in=following)
            if user.nsfw_pref == "HA":
                arts = arts.exclude(nsfw=True)

            return arts.order_by("-created_at")

        else:
            return []


# ------------------------------------------------------------------------------
# User


class JoinView(CreateView):
    template_name = "core/pages/join.html"
    form_class = JoinForm

    def form_valid(self, form):
        user = form.save()

        login(self.request, user)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("core:user", args=[self.request.user.username])


class SignInView(LoginView):
    template_name = "core/pages/sign_in.html"

    def get_success_url(self):
        return reverse("core:user", args=[self.request.user.username])


class SignOutView(LogoutView):
    next_page = reverse_lazy("core:index")


class UserListView(ListView):
    template_name = "core/pages/users.html"
    context_object_name = "users"
    paginate_by = 100

    def get_queryset(self):
        return (
              User.objects
              .order_by("username")
        )


class UserView(TemplateView):
    template_name = "core/pages/user.html"

    def get_context_data(self, username):
        user = get_object_or_404(User, username=username)
        arts = user.art_set.all().order_by("-created_at")

        paginator = Paginator(arts, 25)

        page_no = self.request.GET.get("page", 1)
        try:
            page = paginator.page(page_no)
        except InvalidPage as e:
            raise Http404(f"Invalid page number {page_no}")

        ctx = {
            "user": user,
            "arts": page.object_list,
            "page_obj": page,
        }

        return ctx


class SettingsView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "core/pages/settings.html"
    form_class = SettingsForm
    context_object_name = "user"

    def test_func(self):
        return self.request.user == self.get_object()

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs["username"])

    def get_success_url(self):
        return reverse("core:user", args=[self.get_object().username])


# ------------------------------------------------------------------------------
# Art


class ArtGalleryView(ListView):
    template_name = "core/pages/arts.html"
    context_object_name = "arts"
    paginate_by = 25

    def get_queryset(self):
        arts = Art.objects

        user = self.request.user
        if user.is_authenticated and user.nsfw_pref == "HA":
            arts = arts.exclude(nsfw=True)

        return arts.order_by("-created_at")


class ArtView(TemplateView):
    template_name = "core/pages/art.html"

    def post(self, request, pk):
        if not request.user.is_authenticated:
            raise Http404()

        form = CommentForm(data=request.POST)
        if form.is_valid():
            art = get_object_or_404(Art, pk=pk)
            form.instance.art = art
            form.instance.author = request.user
            form.save()

            return HttpResponseRedirect(reverse("core:art", args=[pk]))

        else:
            return render(request, self.template_name, self.get_context_data(pk, form=form))

    def get_context_data(self, pk, form=None):
        art = get_object_or_404(Art, pk=pk)
        comments = art.comment_set.all().order_by("created_at")

        paginator = Paginator(comments, 25)

        page_no = self.request.GET.get("page", 1)
        try:
            page = paginator.page(page_no)
        except InvalidPage as e:
            raise Http404(f"Invalid page number {page_no}")

        if not form:
            form = CommentForm()

        ctx = {
            "art": art,

            "comments": page.object_list,
            "page_obj": page,

            "form": form,
        }

        return ctx


class PostArtView(LoginRequiredMixin, CreateView):
    template_name = "core/pages/post_art.html"
    form_class = ArtForm

    def form_valid(self, form):
        form.instance.artist = self.request.user

        return super().form_valid(form)


class PostArtView(LoginRequiredMixin, CreateView):
    template_name = "core/pages/post_art.html"
    form_class = ArtForm

    def form_valid(self, form):
        form.instance.artist = self.request.user

        return super().form_valid(form)


class ArtEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "core/pages/edit.html"
    form_class = ArtForm
    context_object_name = "art"

    def test_func(self):
        return self.request.user == self.get_object().artist

    def get_object(self):
        return get_object_or_404(Art, pk=self.kwargs["pk"])


def art_thumb(request, pk):
    art = get_object_or_404(Art, pk=pk)
    image = art.render_thumb()

    # https://help.pythonanywhere.com/pages/FlaskSendFileBytesIO/
    wrapped_image = FileWrapper(image)
    response = HttpResponse(wrapped_image, content_type="image/png")
    response["Content-Disposition"] = 'filename="thumb.png"'

    return response


# ------------------------------------------------------------------------------
# Ajax endpoints


def require_ajax(func):
    def wrapper(request, *args, **kwargs):
        if not request.headers.get("x-requested-with") == "XMLHttpRequest":
            raise Http404()

        response = func(request, *args, **kwargs)

        return response

    return wrapper


@require_ajax
@require_GET
def nsfw_pref(request):
    if not request.user.is_authenticated:
        pref = "AA"
    else:
        pref = request.user.nsfw_pref

    return JsonResponse({"nsfw_pref": pref})



@require_ajax
@require_POST
@login_required
def follow_user(request, username):
    target = get_object_or_404(User, username=username)
    follower = request.user

    follow_user = json.load(request)["follow_user"]
    if follow_user:
        follower.following.add(target)
    else:
        follower.following.remove(target)

    user_followed = target in follower.following.all()

    return JsonResponse({"user_followed": user_followed})


@require_ajax
@require_POST
@login_required
def like_art(request, pk):
    art = get_object_or_404(Art, pk=pk)

    like = json.load(request)["like"]

    if like:
        art.likes.add(request.user)
    else:
        art.likes.remove(request.user)

    like_tally = art.likes.count()
    art_liked = request.user in art.likes.all()

    return JsonResponse({"like_tally": like_tally, "art_liked": art_liked})


@require_ajax
@require_POST
@login_required
def edit_comment(request):
    data = json.load(request)
    comment = get_object_or_404(Comment, pk=data["pk"])
    form = CommentForm(instance=comment, data=data)

    if form.is_valid():
        form.save()

        f_text = linebreaks(comment.text)
        return JsonResponse({ "valid": True, "markup": f_text })

    else:
        response = form.errors
        response.update({ "valid": False })
        return JsonResponse(response)
