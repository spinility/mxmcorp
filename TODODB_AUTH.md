# TodoDB Authentication System 🔐

## Overview

Système d'authentification **léger et gratuit** pour la TodoDB de Cortex, permettant un pool de tâches partagé multi-utilisateurs.

## Architecture

### Stack Technologique
- **SQLite** - Base de données locale (zero-config, gratuit)
- **JWT (JSON Web Tokens)** - Authentification stateless
- **bcrypt** - Hashing sécurisé des mots de passe
- **Python** - Aucune dépendance externe payante

### Composants

```
┌─────────────────┐
│  AuthManager    │  ← Gestion users + JWT tokens
└────────┬────────┘
         │
         ├── auth.db (SQLite)
         │   └── users table
         │
┌────────┴────────┐
│    TodoDB       │  ← Pool de tâches authentifié
└─────────────────┘
         │
         └── todo_pool.db (SQLite)
             ├── tasks table
             └── task_history table
```

## AuthManager (`auth_manager.py`)

### Fonctionnalités

#### 1. **Gestion des Utilisateurs**
- Inscription avec username/password
- Hashage bcrypt (salt auto-généré)
- Rôles: ADMIN, DEVELOPER, VIEWER
- Compte par défaut: `Cortex / cortex123`

#### 2. **Authentification JWT**
- Tokens signés avec secret persistant
- Expiration: 7 jours
- Payload: `user_id`, `username`, `role`, `exp`
- Vérification automatique de l'état du compte

#### 3. **Sécurité**
- Passwords hashés avec bcrypt (industry standard)
- JWT secret généré automatiquement et sauvegardé
- Permissions: `chmod 600` sur le fichier secret
- Comptes activables/désactivables

### API

```python
from cortex.core.auth_manager import create_auth_manager, UserRole

auth = create_auth_manager()

# Inscription
result = auth.register_user(
    username="developer1",
    password="secure_pass",
    role=UserRole.DEVELOPER
)

# Login (obtenir JWT token)
result = auth.login("developer1", "secure_pass")
token = result['token']

# Vérifier token
verify = auth.verify_token(token)
# Returns: {'success': True, 'user_id': 2, 'username': 'developer1', 'role': 'developer'}

# Changer password
auth.change_password(user_id=2, old_password="secure_pass", new_password="new_pass")

# Lister utilisateurs
users = auth.list_users()
```

### Rôles et Permissions

| Rôle | Permissions |
|------|-------------|
| **ADMIN** | Accès complet: créer/modifier/supprimer toutes les tâches |
| **DEVELOPER** | Créer/modifier ses propres tâches, voir toutes les tâches |
| **VIEWER** | Lecture seule sur toutes les tâches |

## TodoDB (`todo_db.py`)

### Fonctionnalités

#### 1. **Pool de Tâches Partagé**
- Multi-utilisateurs avec ownership
- Permissions basées sur les rôles
- Historique d'audit (task_history)
- Statistiques individuelles et globales

#### 2. **Authentification Requise**
Toutes les opérations nécessitent un JWT token valide:
- ✅ Token vérifié automatiquement
- ✅ Permissions checkées par rôle
- ✅ Ownership validée pour modifications

#### 3. **Gestion des Tâches**
- Ajout avec contexte et tier minimum
- Mise à jour de statut
- Assignment à d'autres users
- Filtrage par statut/owner

### API

```python
from cortex.core.todo_db import create_todo_db
from cortex.core.model_router import ModelTier

# Créer TodoDB (partage le même AuthManager)
todo_db = create_todo_db()

# Login d'abord
auth = todo_db.auth
login_result = auth.login("Cortex", "cortex123")
token = login_result['token']

# Ajouter une tâche
result = todo_db.add_task(
    token=token,
    description="Implement OAuth2 authentication",
    context="User requested JWT-based auth with refresh tokens",
    min_tier=ModelTier.DEEPSEEK
)
# Returns: {'success': True, 'task_id': 1, 'message': '...'}

# Lister les tâches
result = todo_db.list_tasks(token)
# Returns: {'success': True, 'tasks': [...], 'count': 10}

# Filtrer par statut
result = todo_db.list_tasks(token, status='pending')

# Filtrer par owner
result = todo_db.list_tasks(token, owner_id=1)

# Obtenir une tâche spécifique
result = todo_db.get_task(token, task_id=1)

# Mettre à jour le statut
result = todo_db.update_task_status(token, task_id=1, new_status='in_progress')

# Statistiques
result = todo_db.get_statistics(token)
# Returns: {
#     'pool_stats': {'total': 50, 'pending': 10, 'completed': 30, ...},
#     'my_stats': {'total': 5, 'completed': 3, ...}
# }
```

## Schéma de Base de Données

### `auth.db` (AuthManager)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'admin', 'developer', 'viewer'
    created_at TEXT NOT NULL,
    last_login TEXT,
    is_active BOOLEAN DEFAULT 1
);
```

### `todo_pool.db` (TodoDB)

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    context TEXT NOT NULL,
    min_tier TEXT NOT NULL,  -- 'nano', 'deepseek', 'claude'
    status TEXT NOT NULL,     -- 'pending', 'in_progress', 'completed', 'blocked'
    owner_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    assigned_to INTEGER,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- 'created', 'status_changed', 'assigned', etc.
    timestamp TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

## Workflow d'Utilisation

### 1. Installation des Dépendances

```bash
pip install PyJWT bcrypt
```

### 2. Première Utilisation

```python
from cortex.core.auth_manager import create_auth_manager
from cortex.core.todo_db import create_todo_db

# Initialisation (crée les DB automatiquement)
auth = create_auth_manager()
todo_db = create_todo_db(auth_manager=auth)

# Login avec compte par défaut
result = auth.login("Cortex", "cortex123")
token = result['token']

print(f"Logged in as: {result['user']['username']}")
print(f"Token: {token[:50]}...")
```

### 3. Créer des Utilisateurs

```python
# Admin crée un développeur
auth.register_user("alice", "alice_secure_pass", UserRole.DEVELOPER)
auth.register_user("bob", "bob_pass", UserRole.DEVELOPER)

# Admin crée un viewer
auth.register_user("observer", "view123", UserRole.VIEWER)
```

### 4. Travailler avec les Tâches

```python
# Alice login
alice_result = auth.login("alice", "alice_secure_pass")
alice_token = alice_result['token']

# Alice crée une tâche
todo_db.add_task(
    token=alice_token,
    description="Add dark mode to UI",
    context="User requested dark theme toggle in settings",
    min_tier=ModelTier.DEEPSEEK
)

# Alice liste ses tâches
my_tasks = todo_db.list_tasks(alice_token, owner_id=alice_result['user']['user_id'])

# Alice met à jour sa tâche
todo_db.update_task_status(alice_token, task_id=1, new_status='in_progress')

# Bob (développeur) peut voir la tâche d'Alice mais pas la modifier
bob_result = auth.login("bob", "bob_pass")
bob_token = bob_result['token']

all_tasks = todo_db.list_tasks(bob_token)  # ✅ Peut lire
# Mais bob_token ne peut pas update la tâche d'Alice ❌

# Admin peut tout modifier
admin_result = auth.login("Cortex", "cortex123")
admin_token = admin_result['token']

todo_db.update_task_status(admin_token, task_id=1, new_status='completed')  # ✅
```

## Sécurité

### Points Forts ✅
- **Pas de plaintext passwords** - bcrypt avec salt auto-généré
- **JWT stateless** - Pas de session server-side
- **Secret persistant** - Généré une seule fois, permissions `600`
- **Token expiration** - 7 jours par défaut
- **Role-based access** - Permissions granulaires
- **Audit trail** - Historique de toutes les actions

### Considérations 🔒
- SQLite = fichier local (pas de connexion réseau nécessaire)
- JWT secret stocké dans `.jwt_secret` (ne pas commit dans git!)
- Ajouter `.jwt_secret` au `.gitignore`
- Changer le password par défaut après installation

## Comparaison avec Alternatives

| Solution | Coût | Complexité | Performance |
|----------|------|------------|-------------|
| **SQLite + JWT** | ✅ Gratuit | ✅ Léger | ✅ Rapide (local) |
| Auth0 | ❌ Payant | ⚠️ Intégration externe | ⚠️ Latence réseau |
| Firebase Auth | ⚠️ Freemium | ⚠️ Vendor lock-in | ⚠️ Latence réseau |
| PostgreSQL + Passport | ✅ Gratuit | ❌ Complexe | ⚠️ Setup lourd |
| OAuth2 Server | ✅ Gratuit | ❌ Très complexe | ⚠️ Maintenance |

## Fichiers Créés

```
cortex/
├── core/
│   ├── auth_manager.py       (448 lignes) - Gestion auth + JWT
│   ├── todo_db.py             (554 lignes) - Pool de tâches authentifié
│   └── ...
├── data/
│   ├── auth.db                (SQLite - users)
│   ├── todo_pool.db           (SQLite - tasks)
│   └── .jwt_secret            (Secret JWT - NE PAS COMMIT!)
└── ...
```

## Tests

```bash
# Tester AuthManager
python3 cortex/core/auth_manager.py

# Tester TodoDB
PYTHONPATH=/github/mxmcorp python3 cortex/core/todo_db.py
```

## Prochaines Étapes (Optionnel)

### Améliorations Possibles
1. **Refresh tokens** - Tokens long-life avec rotation
2. **2FA** - Authentification à deux facteurs
3. **Password reset** - Via email ou code temporaire
4. **Rate limiting** - Protection contre brute-force
5. **Session management** - Révocation de tokens
6. **API REST** - Exposer via Flask/FastAPI

---

**Résumé:** Système complet, léger, gratuit, sécurisé, et prêt à l'emploi! 🎉
