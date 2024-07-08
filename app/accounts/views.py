from actions.models import Action
from actions.utils import create_action
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ProfileEditForm, UserEditForm, UserRegistrationForm
from .models import Contact, Profile

User = get_user_model()


@login_required
def user_list(request):
    users = User.objects.filter(is_active=True)
    context = {"section": "people", "users": users}
    return render(request, "accounts/users/list.html", context)


@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    context = {"section": "people", "user": user}
    return render(request, "accounts/users/detail.html", context)


@login_required
@require_POST
def user_follow(request):
    user_id = request.POST.get("id")
    action = request.POST.get("action")

    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if request.user.id != user.id:
                if action == "follow":
                    Contact.objects.get_or_create(user_from=request.user, user_to=user)
                    create_action(request.user, "is following", user)
                else:
                    Contact.objects.filter(
                        user_from=request.user, user_to=user
                    ).delete()
                return JsonResponse({"status": "ok"})
            else:
                return JsonResponse({"status": "error"})

        except User.DoesNotExist:
            return JsonResponse({"status": "error"})

    return JsonResponse({"status": "error"})


def register(request):
    if request.method == "POST":
        user_form = UserRegistrationForm(data=request.POST)
        if user_form.is_valid():
            # Create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data["password"])
            # Save the User object
            new_user.save()
            # Create the user profile
            Profile.objects.create(user=new_user)
            create_action(new_user, "has created an account")
            messages.success(request, "Successfully registered")
            return render(
                request, "accounts/register_done.html", {"new_user": new_user}
            )

        else:
            messages.error(request, "Error registering your account")

    else:
        user_form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"user_form": user_form})


@login_required
def dashboard(request):
    # Display all actions by default
    actions = Action.objects.exclude(user=request.user)
    following_ids = request.user.following.values_list("id", flat=True)

    if following_ids:
        actions = actions.filter(user_id__in=following_ids)
    actions = actions.select_related("user", "user__profile").prefetch_related(
        "target"
    )[:10]

    context = {"section": "dashboard", "actions": actions}
    return render(request, "accounts/dashboard.html", context)


@login_required
def edit(request):
    if request.method == "POST":
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(
            instance=request.user.profile, data=request.POST, files=request.FILES
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully")
            return redirect(reverse("accounts:dashboard"))

        else:
            messages.error(request, "Error updating your profile")

    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)

    context = {"user_form": user_form, "profile_form": profile_form}

    return render(request, "accounts/edit.html", context)
