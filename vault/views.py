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
    """Affiche la page d'accueil publique de l'application."""

    return render(request, "vault/home.html")


@require_http_methods(["GET", "POST"])
def register_view(request):
    """Gere l'inscription d'un nouvel utilisateur."""

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
    """Authentifie l'utilisateur puis initialise une verification OTP."""

    if request.user.is_authenticated:
        return redirect("dashboard" if request.session.get("otp_verified") else "verify_otp")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)

        # Un OTP temporaire est stocke en session jusqu'a sa validation.
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
    """Valide le code OTP avant d'autoriser l'acces au coffre."""

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

        # Le code est invalide au-dela de la duree configuree dans settings.py.
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
            "otp_code": request.session.get("otp_code"),
            "otp_validity_seconds": settings.OTP_VALIDITY_SECONDS,
        },
    )


@login_required
def logout_view(request):
    """Deconnecte l'utilisateur et nettoie les informations OTP de session."""

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
    """Affiche un resume du coffre de l'utilisateur connecte."""

    entries = PasswordEntry.objects.filter(user=request.user)
    context = {
        "entry_count": entries.count(),
        "recent_entries": entries.order_by("-updated_at")[:5],
    }
    return render(request, "vault/dashboard.html", context)


@login_required
@otp_required
def password_list(request):
    """Liste toutes les entrees de mot de passe de l'utilisateur."""

    entries = PasswordEntry.objects.filter(user=request.user)
    return render(request, "vault/password_list.html", {"entries": entries})


@login_required
@otp_required
@require_http_methods(["GET", "POST"])
def password_create(request):
    """Cree une nouvelle entree apres chiffrement du mot de passe saisi."""

    form = PasswordEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        # Le champ plain_password vient du formulaire et n'est jamais stocke tel quel.
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
    """Affiche le detail d'une entree avec son mot de passe dechiffre."""

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
    """Met a jour une entree et rechiffre le mot de passe si necessaire."""

    entry = _get_user_entry(request, pk)
    form = PasswordEntryForm(request.POST or None, instance=entry, is_update=True)
    if request.method == "POST" and form.is_valid():
        updated_entry = form.save(commit=False)
        new_password = form.cleaned_data["plain_password"]
        # En modification, un champ vide conserve l'ancien mot de passe chiffre.
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
    """Supprime une entree apres confirmation par formulaire POST."""

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
    """Genere un mot de passe selon les options choisies par l'utilisateur."""

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
