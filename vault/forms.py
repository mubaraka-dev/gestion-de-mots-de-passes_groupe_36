import string

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import PasswordEntry


class BootstrapFormMixin:
    """Ajoute automatiquement les classes Bootstrap 4 aux widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    """Formulaire d'inscription avec l'adresse e-mail obligatoire."""

    email = forms.EmailField(required=True)

    class Meta:
        """Associe le formulaire au modele utilisateur natif de Django."""

        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        """Enregistre l'utilisateur en ajoutant l'e-mail au modele Django."""

        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    """Formulaire de connexion base sur l'authentification Django."""

    username = forms.CharField(widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(widget=forms.PasswordInput())


class OTPVerificationForm(BootstrapFormMixin, forms.Form):
    """Formulaire de saisie du code OTP a six chiffres."""

    otp_code = forms.CharField(
        label="Code OTP",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={"placeholder": "Ex. 123456"}),
    )


class PasswordEntryForm(BootstrapFormMixin, forms.ModelForm):
    """Formulaire de creation et modification d'une entree du coffre.

    Le champ ``plain_password`` sert uniquement a recevoir le mot de passe en
    clair depuis l'interface. Il n'est pas sauvegarde directement dans le modele.
    """

    plain_password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(render_value=True),
        help_text="Le mot de passe saisi sera chiffre avant l'enregistrement.",
        required=False,
    )

    class Meta:
        """Champs exposes a l'utilisateur pour une entree de mot de passe."""

        model = PasswordEntry
        fields = ("service_name", "username", "plain_password", "note")
        widgets = {
            "note": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        """Rend le mot de passe obligatoire uniquement a la creation."""

        self.is_update = kwargs.pop("is_update", False)
        super().__init__(*args, **kwargs)
        if not self.is_update:
            self.fields["plain_password"].required = True
        else:
            self.fields["plain_password"].help_text = (
                "Laissez vide pour conserver le mot de passe deja enregistre."
            )

    def clean_plain_password(self):
        """Verifie qu'un nouveau mot de passe est fourni lors d'une creation."""

        password = self.cleaned_data.get("plain_password", "")
        if not password and not self.is_update:
            raise forms.ValidationError("Veuillez saisir un mot de passe.")
        return password


class PasswordGeneratorForm(BootstrapFormMixin, forms.Form):
    """Parametres utilises pour generer un mot de passe robuste."""

    length = forms.IntegerField(
        label="Longueur",
        min_value=8,
        max_value=64,
        initial=16,
    )
    include_uppercase = forms.BooleanField(label="Majuscules", required=False, initial=True)
    include_lowercase = forms.BooleanField(label="Minuscules", required=False, initial=True)
    include_digits = forms.BooleanField(label="Chiffres", required=False, initial=True)
    include_special = forms.BooleanField(
        label="Caracteres speciaux",
        required=False,
        initial=True,
    )

    def clean(self):
        """Controle la coherence entre la longueur et les types de caracteres."""

        cleaned_data = super().clean()
        choices = [
            cleaned_data.get("include_uppercase"),
            cleaned_data.get("include_lowercase"),
            cleaned_data.get("include_digits"),
            cleaned_data.get("include_special"),
        ]
        selected_groups = sum(bool(choice) for choice in choices)
        if selected_groups == 0:
            raise forms.ValidationError("Choisissez au moins un type de caracteres.")
        if cleaned_data.get("length", 0) < selected_groups:
            raise forms.ValidationError(
                "La longueur doit etre au moins egale au nombre de types choisis."
            )
        return cleaned_data

    @staticmethod
    def character_sets():
        """Retourne les ensembles de caracteres disponibles pour la generation."""

        return {
            "include_uppercase": string.ascii_uppercase,
            "include_lowercase": string.ascii_lowercase,
            "include_digits": string.digits,
            "include_special": string.punctuation,
        }
