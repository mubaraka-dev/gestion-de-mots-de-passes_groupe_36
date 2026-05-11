"""
Django settings for gestionnaire project.

Configuration pedagogique pour un TP de coffre-fort web de mots de passe.
"""

import os
from pathlib import Path


# Chemin racine du projet. Il sert a construire les chemins vers la base SQLite,
# les fichiers statiques et les templates.
BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(path):
    """Charge les variables simples KEY=VALUE depuis un fichier .env."""
    if not path.exists():
        return

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file(BASE_DIR / ".env")


# Cle secrete Django utilisee pour signer les cookies, les sessions et certains
# jetons de securite. Elle est chargee depuis le fichier .env a la racine.
SECRET_KEY = os.environ.get("SECRET_KEY")

# Mode debug active pour faciliter le developpement local. A desactiver en
# production afin de ne pas exposer les erreurs internes de l'application.
DEBUG = True

# Liste des noms de domaine autorises a servir l'application. Vide ici car le
# projet est prevu pour une execution locale pendant le TP.
ALLOWED_HOSTS = ['*']


# Applications Django activees. Les modules natifs fournissent l'administration,
# l'authentification, les sessions, les messages et les fichiers statiques.
# L'application locale `vault` contient la logique du coffre-fort.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "vault",
]

# Chaine de middlewares appliquee a chaque requete HTTP.
# Ces composants activent notamment les protections de securite natives :
# - SecurityMiddleware ajoute des en-tetes de securite ;
# - SessionMiddleware gere la session utilisateur ;
# - CsrfViewMiddleware bloque les formulaires sans jeton CSRF valide ;
# - AuthenticationMiddleware attache l'utilisateur connecte a la requete ;
# - XFrameOptionsMiddleware limite le clickjacking.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gestionnaire.urls"

# Configuration du moteur de templates Django. `APP_DIRS=True` permet de charger
# automatiquement les templates places dans `vault/templates/`.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "gestionnaire.wsgi.application"


# Base de donnees locale SQLite. Les vues utilisent l'ORM Django, ce qui evite
# de construire des requetes SQL a la main et limite les risques d'injection SQL.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Validateurs natifs appliques aux mots de passe des comptes utilisateur Django.
# Ils refusent notamment les mots de passe trop courts, trop communs ou
# uniquement numeriques.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Parametres de langue et fuseau horaire utilises pour l'affichage des dates et
# messages de l'application.
LANGUAGE_CODE = "fr-fr"

TIME_ZONE = "Africa/Kinshasa"

USE_I18N = True

USE_TZ = True


# Configuration des fichiers statiques, par exemple `static/css/styles.css`.
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Routes utilisees par Django pour rediriger automatiquement les utilisateurs
# selon leur etat d'authentification.
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "verify_otp"
LOGOUT_REDIRECT_URL = "home"


# Cle Fernet utilisee pour chiffrer et dechiffrer les mots de passe stockes dans
# le coffre. Elle doit rester stable pour pouvoir relire les mots de passe deja
# chiffres.
FERNET_KEY = os.environ.get("FERNET_KEY")

# Duree de validite du code OTP en secondes. Avec 300 secondes, l'utilisateur a
# 5 minutes pour saisir le code avant qu'il soit supprime de la session et que la
# connexion soit refusee.
OTP_VALIDITY_SECONDS = 300
