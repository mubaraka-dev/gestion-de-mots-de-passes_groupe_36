import secrets

from cryptography.fernet import Fernet
from django.conf import settings

from .forms import PasswordGeneratorForm


def _get_cipher():
    """Construit l'instance Fernet a partir de la configuration Django."""

    key = settings.FERNET_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_password(plain_password):
    """Chiffre un mot de passe avant stockage en base."""

    return _get_cipher().encrypt(plain_password.encode()).decode()


def decrypt_password(encrypted_password):
    """Dechiffre un mot de passe pour l'affichage controle."""

    return _get_cipher().decrypt(encrypted_password.encode()).decode()


def generate_otp_code():
    """Genere un OTP numerique a 6 chiffres pour le second facteur."""

    return f"{secrets.randbelow(1_000_000):06d}"


def generate_secure_password(cleaned_data):
    """Genere un mot de passe aleatoire cote serveur selon les options choisies."""

    pools = []
    for field_name, characters in PasswordGeneratorForm.character_sets().items():
        if cleaned_data.get(field_name):
            pools.append(characters)

    rng = secrets.SystemRandom()
    password_chars = [rng.choice(pool) for pool in pools]
    combined_pool = "".join(pools)

    while len(password_chars) < cleaned_data["length"]:
        password_chars.append(rng.choice(combined_pool))

    rng.shuffle(password_chars)
    return "".join(password_chars)
