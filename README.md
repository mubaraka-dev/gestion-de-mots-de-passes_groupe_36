# Vault Web - Generateur et gestionnaire de mots de passe securise

## Presentation du sujet

Vault Web est une application Django de TP qui permet de stocker et gerer des mots de passe de maniere securisee. Le projet combine trois aspects importants de la securite applicative :

- l'authentification utilisateur avec le systeme natif de Django ;
- un second facteur OTP apres la connexion ;
- le chiffrement des mots de passe stockes avec Fernet, un mecanisme reposant sur AES.

L'objectif est de proposer une application simple et fonctionnelle en local avec SQLite.

## Technologies utilisees

- Python 3
- Django
- SQLite
- Cryptography
- HTML / CSS
- Bootstrap 4

## Fonctionnalites

- inscription d'un utilisateur ;
- connexion avec nom d'utilisateur et mot de passe ;
- verification OTP obligatoire apres connexion ;
- affichage du code OTP dans la console du serveur pour le TP ;
- tableau de bord apres validation OTP ;
- ajout d'une entree de mot de passe ;
- liste des mots de passe de l'utilisateur connecte ;
- detail avec dechiffrement controle ;
- modification et suppression avec verification de propriete ;
- generateur de mots de passe cote backend ;
- messages de succes et d'erreur avec Django messages framework.

## Architecture du projet

```text
gestionnaire-MP/
├── gestionnaire/          # Configuration principale Django
├── vault/                 # Application metier du coffre-fort
│   ├── migrations/
│   ├── templates/vault/   # Templates Bootstrap 4
│   ├── admin.py
│   ├── decorators.py      # Protection OTP
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── utils.py           # Chiffrement Fernet et generation
│   └── views.py
├── static/css/styles.css  # Style global
├── db.sqlite3             # Cree apres migration
└── README.md
```

## Installation

1. Creer et activer un environnement virtuel si necessaire.
2. Installer les dependances :

```bash
pip install django cryptography
```

3. Generer une cle Fernet si vous souhaitez remplacer la cle de demonstration :

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. Exporter la cle dans la variable d'environnement `FERNET_KEY` si souhaite :

```bash
export FERNET_KEY="votre_cle_fernet"
```

## Commandes de lancement

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ensuite, ouvrir `http://127.0.0.1:8000/`.

## Chiffrement AES / Fernet

Le projet utilise la bibliotheque `cryptography` et le module `Fernet`.

- Fernet repose sur AES pour assurer la confidentialite des donnees.
- Fernet ajoute egalement une verification d'integrite et d'authenticite.
- Le mot de passe n'est jamais stocke en clair dans la base SQLite.
- Lors de la creation ou modification d'une entree, le mot de passe est chiffre avant sauvegarde.
- Le dechiffrement n'a lieu que dans la vue de detail, apres authentification et verification OTP.

Fonctions principales dans `vault/utils.py` :

- `encrypt_password(plain_password)`
- `decrypt_password(encrypted_password)`

## Authentification forte OTP

Apres une connexion reussie :

1. l'utilisateur est authentifie par Django ;
2. un code OTP a 6 chiffres est genere ;
3. le code OTP est stocke temporairement dans la session ;
4. le code est affiche dans la console du serveur pour le TP ;
5. l'utilisateur doit saisir le bon code sur la page de verification ;
6. si le code est correct, la session stocke `otp_verified=True`.

Tant que l'OTP n'est pas valide, l'acces au coffre et aux routes sensibles reste bloque.

## Scenario de test complet

1. Lancer le serveur avec `python manage.py runserver`.
2. Ouvrir l'application dans le navigateur.
3. Creer un compte avec la page d'inscription.
4. Se connecter avec le compte cree.
5. Observer dans la console du serveur le code OTP affiche.
6. Saisir ce code dans la page de verification OTP.
7. Acceder au tableau de bord.
8. Ajouter une entree de mot de passe.
9. Verifier que la liste n'affiche jamais le mot de passe en clair.
10. Ouvrir la page detail pour voir le mot de passe dechiffre.
11. Modifier l'entree puis tester la suppression.
12. Tester le generateur de mot de passe.
13. Verifier qu'un utilisateur ne voit jamais les entrees d'un autre utilisateur.

## Securite minimale mise en place

- protection CSRF sur tous les formulaires ;
- `login_required` sur les vues sensibles ;
- decorateur OTP pour bloquer l'acces tant que le second facteur n'est pas valide ;
- verification stricte de proprietaire avec `request.user` ;
- aucun stockage de mot de passe en clair ;
- distinction entre le mot de passe du compte Django et les mots de passe stockes dans le coffre.

### Protection native Django : CSRF, XSS et injections SQL

Le projet s'appuie sur les mecanismes natifs de Django pour reduire les risques
classiques des applications web.

Dans `gestionnaire/settings.py`, la liste `MIDDLEWARE` active notamment :

- `django.middleware.security.SecurityMiddleware`, pour appliquer des protections
  HTTP de base ;
- `django.contrib.sessions.middleware.SessionMiddleware`, pour gerer les sessions
  utilisateur ;
- `django.middleware.csrf.CsrfViewMiddleware`, pour bloquer les requetes POST
  sans jeton CSRF valide ;
- `django.middleware.clickjacking.XFrameOptionsMiddleware`, pour limiter le
  clickjacking.

Les formulaires HTML contiennent le jeton CSRF avec `{% csrf_token %}`. On le
retrouve par exemple dans les templates `login.html`, `register.html`,
`verify_otp.html`, `password_form.html`, `password_generator.html` et
`password_confirm_delete.html`.

Pour les attaques XSS, les templates Django echappent automatiquement les
variables affichees avec `{{ ... }}`. Les valeurs utilisateur comme
`{{ entry.service_name }}`, `{{ entry.username }}` ou `{{ entry.note }}` sont donc
affichees comme du texte et non interpretees comme du HTML. Le projet n'utilise
pas `|safe`, `mark_safe` ou `autoescape off`.

Pour les injections SQL, le projet utilise l'ORM Django au lieu de construire des
requetes SQL a la main. Les acces aux donnees passent par des appels comme :

```python
PasswordEntry.objects.filter(user=request.user)
get_object_or_404(PasswordEntry, pk=pk, user=request.user)
```

Django parametre alors les requetes SQL generees et evite l'injection par
concatenation de chaines.

### Sessions securisees et expiration automatique

Les sessions sont activees par `SessionMiddleware` dans `gestionnaire/settings.py`.
Elles servent notamment a stocker temporairement l'etat de verification OTP :

```python
request.session["otp_code"] = otp_code
request.session["otp_generated_at"] = time.time()
request.session["otp_verified"] = False
```

L'application impose une expiration automatique du code OTP avec
`OTP_VALIDITY_SECONDS = 300`, soit 5 minutes. Lors de la verification, si le code
est trop ancien, les informations OTP sont retirees de la session et
l'utilisateur est deconnecte :

```python
if time.time() - generated_at > settings.OTP_VALIDITY_SECONDS:
    request.session.pop("otp_code", None)
    request.session.pop("otp_generated_at", None)
    request.session["otp_verified"] = False
    logout(request)
```

Cela protege l'acces au coffre apres la connexion : meme si l'utilisateur a
fourni un nom d'utilisateur et un mot de passe corrects, il doit valider un OTP
encore valide avant d'acceder aux vues sensibles protegees par `otp_required`.

Remarque : le projet ne definit pas encore de reglage explicite comme
`SESSION_COOKIE_AGE` ou `SESSION_EXPIRE_AT_BROWSER_CLOSE`. L'expiration stricte
documentee ici concerne donc le code OTP ; l'expiration generale de session reste
celle fournie par Django par defaut.

## Limites du TP

- l'OTP est affiche dans la console et non envoye par SMS ou email ;
- la cle Fernet  est laissee dans `settings.py` pour la demonstration ;
- le projet utilise SQLite, adapte a un TP mais pas a une production ;
- le mot de passe dechiffre est visible sur la page de detail ;
- aucune journalisation avancee ni rotation de cle n'est implemente.

## Ameliorations possibles

- envoyer l'OTP par email ou application mobile ;
- stocker la cle Fernet uniquement dans des variables d'environnement ;
- ajouter une copie securisee dans le presse-papiers ;
- introduire une expiration de session plus stricte ;
- renforcer les journaux de securite ;
- ajouter des tests automatises pour les vues, formulaires et controles d'acces.




login: 
mp: 3messiers89

