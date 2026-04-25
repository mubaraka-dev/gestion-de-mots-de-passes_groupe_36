from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def otp_required(view_func):
    """Autorise l'acces seulement si l'utilisateur a valide son OTP."""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if request.session.get("otp_verified"):
            return view_func(request, *args, **kwargs)
        messages.warning(request, "Veuillez valider votre code OTP pour acceder au coffre.")
        return redirect("verify_otp")

    return _wrapped_view
