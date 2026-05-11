from django.apps import AppConfig


class VaultConfig(AppConfig):
    """Configuration Django de l'application de gestion du coffre."""

    # Type de cle primaire genere automatiquement pour les nouveaux modeles.
    default_auto_field = "django.db.models.BigAutoField"
    name = "vault"
