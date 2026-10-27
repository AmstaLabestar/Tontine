# Tontine - Application Mobile Offline-First

## Description

Application mobile de gestion de tontine avec fonctionnement hors ligne, synchronisation fiable et transparence totale des contributions.

## Architecture

### Backend (Django REST Framework)
- Python 3.14+
- Django 6.x
- Django REST Framework 3.18
- PostgreSQL (production) / SQLite (développement)
- JWT Authentication

### Mobile (Flutter)
- Flutter 3.x
- Riverpod (state management)
- Drift (SQLite local)
- Dio (HTTP client)

## Structure du projet

```
Tontine/
├── backend/           # Django REST API
│   ├── accounts/      # Authentification et utilisateurs
│   ├── groups/        # Groupes de tontine
│   ├── members/       # Membres
│   ├── contributions/ # Contributions et corrections
│   ├── audit/         # Journal d'audit
│   ├── sync/          # Synchronisation
│   └── vault/         # Vérification physique du coffre
├── mobile/            # Application Flutter
│   └── lib/
│       ├── core/      # Thème, constantes, utils
│       ├── data/      # Modèles, repositories, DB locale
│       └── presentation/  # Écrans et widgets
├── docs/              # Documentation
└── scripts/           # Scripts utilitaires
```

## Lancement local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Variables d'environnement

Copier `.env.example` vers `.env` et configurer :

```
SECRET_KEY=your-secret-key
DEBUG=True
DB_ENGINE=sqlite  # ou postgres
```

### Mobile

```bash
cd mobile
flutter pub get
flutter run
```

## API Endpoints

### Authentification
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion (JWT)
- `POST /api/auth/refresh/` - Rafraîchir le token
- `POST /api/auth/logout/` - Déconnexion
- `GET /api/auth/profile/` - Profil utilisateur

### Groupes
- `GET/POST /api/groups/` - Liste/Créer des groupes
- `GET/PUT/DELETE /api/groups/{id}/` - Détail d'un groupe
- `GET/POST /api/groups/{id}/members/` - Membres du groupe
- `GET/POST /api/groups/{id}/tontine-members/` - Membres de la tontine
- `GET/POST /api/groups/{id}/contributions/` - Contributions
- `POST /api/groups/{id}/contributions/{id}/transition/` - Changer le statut
- `POST /api/groups/{id}/contributions/{id}/correct/` - Corriger
- `GET /api/groups/{id}/audit/` - Journal d'audit
- `GET/POST /api/groups/{id}/vault/` - Vérification du coffre
- `POST /api/groups/{id}/vault/{id}/resolve/` - Résoudre un écart
- `POST /api/groups/{id}/sync/push/` - Pousser des opérations
- `GET /api/groups/{id}/sync/pull/` - Récupérer des opérations
- `GET /api/groups/{id}/sync/status/` - Statut de sync

## Tests

```bash
cd backend
python manage.py test
```

## Limites connues

1. La synchronisation en temps réel entre appareils nécessite une connexion Internet.
2. Les opérations enregistrées hors ligne sur un appareil perdu ne peuvent pas être récupérées.
3. La double validation n'est pas une preuve absolue contre la fraude.
4. Le solde numérique ne garantit pas la présence physique de l'argent dans le coffre.
5. Flutter SDK n'est pas inclus dans cet environnement de développement.

## Sécurité

- Authentification JWT avec rotation des refresh tokens
- Limitation des tentatives de connexion (throttling)
- Audit trail immuable
- Validation stricte des entrées
- HTTPS requis en production
- Révocation des appareils perdus
