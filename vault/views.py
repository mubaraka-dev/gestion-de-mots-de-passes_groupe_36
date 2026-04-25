import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .decorators import otp_required
from .forms import (
    LoginForm,
    OTPVerificationForm,
    PasswordEntryForm,
    PasswordGeneratorForm,
    RegisterForm,
)
from .models import PasswordEntry
from .utils import decrypt_password, encrypt_password, generate_otp_code, generate_secure_password


def home(request):
    return render(request, "vault/home.html")


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard" if request.session.get("otp_verified") else "verify_otp")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Compte cree avec succes. Vous pouvez maintenant vous connecter.")
        return redirect("login")
    return render(request, "vault/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard" if request.session.get("otp_verified") else "verify_otp")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)

        otp_code = generate_otp_code()
        request.session["otp_code"] = otp_code
        request.session["otp_generated_at"] = time.time()
        request.session["otp_verified"] = False

        # Pour le TP, le code OTP est affiche dans la console du serveur.
        print(f"[OTP DEBUG] Utilisateur={user.username} Code OTP={otp_code}")

        messages.info(
            request,
            "Connexion reussie. Saisissez maintenant le code OTP affiche dans la console.",
        )
        return redirect("verify_otp")
    return render(request, "vault/login.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def verify_otp_view(request):
    if request.session.get("otp_verified"):
        return redirect("dashboard")

    if "otp_code" not in request.session:
        logout(request)
        messages.error(request, "Aucun OTP actif. Veuillez vous reconnecter.")
        return redirect("login")

    form = OTPVerificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        submitted_code = form.cleaned_data["otp_code"]
        expected_code = request.session.get("otp_code")
        generated_at = request.session.get("otp_generated_at", 0)

        if time.time() - generated_at > settings.OTP_VALIDITY_SECONDS:
            request.session.pop("otp_code", None)
            request.session.pop("otp_generated_at", None)
            request.session["otp_verified"] = False
            logout(request)
            messages.error(request, "Le code OTP a expire. Reconnectez-vous pour en recevoir un autre.")
            return redirect("login")

        if submitted_code != expected_code:
            messages.error(request, "Code OTP invalide.")
        else:
            request.session["otp_verified"] = True
            request.session.pop("otp_code", None)
            request.session.pop("otp_generated_at", None)
            messages.success(request, "OTP valide. Acces au coffre autorise.")
            return redirect("dashboard")

    return render(
        request,
        "vault/verify_otp.html",
        {
            "form": form,
            "otp_validity_seconds": settings.OTP_VALIDITY_SECONDS,
        },
    )


@login_required
def logout_view(request):
    request.session.pop("otp_code", None)
    request.session.pop("otp_generated_at", None)
    request.session.pop("otp_verified", None)
    logout(request)
    messages.info(request, "Vous avez ete deconnecte.")
    return redirect("home")


def _get_user_entry(request, pk):
    """Recupere une entree seulement si elle appartient a l'utilisateur connecte."""

    return get_object_or_404(PasswordEntry, pk=pk, user=request.user)


@login_required
@otp_required
def dashboard(request):
    entries = PasswordEntry.objects.filter(user=request.user)
    context = {
        "entry_count": entries.count(),
        "recent_entries": entries.order_by("-updated_at")[:5],
    }
    return render(request, "vault/dashboard.html", context)


@login_required
@otp_required
def password_list(request):
    entries = PasswordEntry.objects.filter(user=request.user)
    return render(request, "vault/password_list.html", {"entries": entries})


@login_required
@otp_required
@require_http_methods(["GET", "POST"])
def password_create(request):
    form = PasswordEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.encrypted_password = encrypt_password(form.cleaned_data["plain_password"])
        entry.save()
        messages.success(request, "Mot de passe ajoute et chiffre avec succes.")
        return redirect("password_list")
    return render(
        request,
        "vault/password_form.html",
        {"form": form, "page_title": "Ajouter un mot de passe", "submit_label": "Enregistrer"},
    )


@login_required
@otp_required
def password_detail(request, pk):
    entry = _get_user_entry(request, pk)
    decrypted_password = decrypt_password(entry.encrypted_password)
    return render(
        request,
        "vault/password_detail.html",
        {"entry": entry, "decrypted_password": decrypted_password},
    )


@login_required
@otp_required
@require_http_methods(["GET", "POST"])
def password_update(request, pk):
    entry = _get_user_entry(request, pk)
    form = PasswordEntryForm(request.POST or None, instance=entry, is_update=True)
    if request.method == "POST" and form.is_valid():
        updated_entry = form.save(commit=False)
        new_password = form.cleaned_data["plain_password"]
        if new_password:
            updated_entry.encrypted_password = encrypt_password(new_password)
        updated_entry.user = request.user
        updated_entry.save()
        messages.success(request, "Entree mise a jour avec succes.")
        return redirect("password_detail", pk=entry.pk)
    return render(
        request,
        "vault/password_form.html",
        {"form": form, "page_title": "Modifier un mot de passe", "submit_label": "Mettre a jour"},
    )


@login_required
@otp_required
@require_http_methods(["GET", "POST"])
def password_delete(request, pk):
    entry = _get_user_entry(request, pk)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Entree supprimee avec succes.")
        return redirect("password_list")
    return render(request, "vault/password_confirm_delete.html", {"entry": entry})


@login_required
@otp_required
@require_http_methods(["GET", "POST"])
def password_generator(request):
    generated_password = None
    form = PasswordGeneratorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        generated_password = generate_secure_password(form.cleaned_data)
        messages.success(request, "Mot de passe genere avec succes.")
    return render(
        request,
        "vault/password_generator.html",
        {"form": form, "generated_password": generated_password},
    )
