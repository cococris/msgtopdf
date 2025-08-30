# API de Conversion MSG vers PDF

Une API FastAPI robuste pour convertir les fichiers .msg Outlook en PDF avec validation JWT et fusion des pièces jointes PDF.

## 🚀 Fonctionnalités

- **Conversion MSG vers PDF** : Convertit les emails Outlook (.msg) en documents PDF formatés
- **Authentification JWT** : Validation des tokens JWT avec récupération des clés publiques via JWKS
- **Fusion des pièces jointes** : Merge automatique des PDFs en pièces jointes avec le mail converti
- **Filtrage des pièces jointes** : Accepte uniquement les PDFs, refuse les autres types de fichiers
- **Logging complet** : Système de logging détaillé avec couleurs et niveaux configurables
- **Tests unitaires** : Suite de tests complète avec pytest
- **Documentation automatique** : Documentation Swagger/OpenAPI intégrée

## 📋 Prérequis

- Python 3.8+
- pip ou poetry pour la gestion des dépendances

## 🛠️ Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd msg_to_pdf_api
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration**
```bash
cp .env.example .env
# Éditer le fichier .env avec vos paramètres
```

## ⚙️ Configuration

Créez un fichier `.env` basé sur `.env.example` :

```env
# Configuration JWT
JWKS_URL=https://your-auth-provider.com/.well-known/jwks.json
JWT_AUDIENCE=your-api-audience
JWT_ISSUER=https://your-auth-provider.com/

# Configuration de l'application
LOG_LEVEL=INFO
TEMP_DIR=/tmp
```

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `JWKS_URL` | URL des clés publiques JWKS | - |
| `JWT_AUDIENCE` | Audience attendue dans le JWT | - |
| `JWT_ISSUER` | Émetteur attendu dans le JWT | - |
| `LOG_LEVEL` | Niveau de logging (DEBUG, INFO, WARNING, ERROR) | INFO |
| `TEMP_DIR` | Répertoire temporaire pour les fichiers | /tmp |

## 🚀 Démarrage

### Mode développement
```bash
python -m app.main
```

### Mode production avec Uvicorn
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Avec Docker (optionnel)
```bash
# Créer l'image
docker build -t msg-to-pdf-api .

# Lancer le conteneur
docker run -p 8000:8000 --env-file .env msg-to-pdf-api
```

## 📚 Utilisation de l'API

### Authentification

Toutes les requêtes (sauf `/health`) nécessitent un token JWT valide :

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -X GET http://localhost:8000/user/info
```

### Endpoints disponibles

#### 🏥 Santé de l'API
```http
GET /health
```

Retourne le statut de l'API et la connectivité JWKS.

#### 👤 Informations utilisateur
```http
GET /user/info
Authorization: Bearer <token>
```

Retourne les informations de l'utilisateur connecté.

#### 🔄 Conversion MSG vers PDF
```http
POST /convert
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <fichier.msg>
merge_attachments: true|false (optionnel, défaut: true)
```

**Exemple avec curl :**
```bash
curl -X POST "http://localhost:8000/convert" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "file=@email.msg" \
     -F "merge_attachments=true" \
     --output converted.pdf
```

**Réponse :**
- **200 OK** : PDF généré (binaire)
- **400 Bad Request** : Fichier invalide ou manquant
- **401 Unauthorized** : Token JWT invalide
- **413 Payload Too Large** : Fichier trop volumineux (>50MB)
- **422 Unprocessable Entity** : Erreur de conversion
- **500 Internal Server Error** : Erreur interne

**Headers de réponse :**
- `Content-Disposition`: Nom du fichier PDF
- `X-Request-ID`: Identifiant unique de la requête
- `X-Processing-Time`: Temps de traitement en secondes
- `X-Attachments-Processed`: Nombre de PDFs fusionnés
- `X-Original-Size`: Taille du fichier original
- `X-Output-Size`: Taille du PDF généré

## 🧪 Tests

### Lancer tous les tests
```bash
pytest
```

### Tests avec couverture
```bash
pytest --cov=app --cov-report=html
```

### Tests spécifiques
```bash
# Tests d'authentification
pytest tests/test_auth.py

# Tests de conversion
pytest tests/test_msg_converter.py

# Tests API
pytest tests/test_api.py
```

## 📖 Documentation

### Documentation interactive
Une fois l'API démarrée, accédez à :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Structure du projet
```
msg_to_pdf_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application FastAPI principale
│   ├── config.py            # Configuration
│   ├── auth.py              # Authentification JWT/JWKS
│   ├── models.py            # Modèles Pydantic
│   ├── logging_config.py    # Configuration du logging
│   └── services/
│       ├── __init__.py
│       └── msg_converter.py # Service de conversion MSG
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Configuration des tests
│   ├── test_auth.py         # Tests d'authentification
│   ├── test_msg_converter.py # Tests de conversion
│   └── test_api.py          # Tests des endpoints
├── requirements.txt         # Dépendances Python
├── .env.example            # Exemple de configuration
└── README.md               # Cette documentation
```

## 🔒 Sécurité

### Authentification JWT
- Validation des tokens JWT avec vérification de signature
- Récupération automatique des clés publiques via JWKS
- Cache des clés JWKS (1 heure) pour optimiser les performances
- Support des algorithmes RS256

### Validation des fichiers
- Vérification de l'extension (.msg uniquement)
- Limite de taille de fichier (50MB par défaut)
- Validation du type MIME
- Nettoyage automatique des fichiers temporaires

### Logging de sécurité
- Logging de toutes les tentatives d'authentification
- Traçabilité des requêtes avec ID unique
- Logging des erreurs avec contexte
- Pas de logging des données sensibles

## 🐛 Dépannage

### Erreurs courantes

**Erreur JWKS**
```
JWTError: Impossible de récupérer les clés JWKS
```
- Vérifiez l'URL JWKS dans la configuration
- Vérifiez la connectivité réseau
- Vérifiez que le serveur JWKS est accessible

**Erreur de conversion**
```
MSGConversionError: Erreur de conversion
```
- Vérifiez que le fichier est un vrai fichier .msg
- Vérifiez que le fichier n'est pas corrompu
- Vérifiez les permissions de lecture

**Token JWT invalide**
```
JWTError: Token invalide
```
- Vérifiez que le token n'est pas expiré
- Vérifiez l'audience et l'émetteur du token
- Vérifiez que les clés JWKS correspondent

### Logs de débogage

Activez le mode debug dans `.env` :
```env
LOG_LEVEL=DEBUG
```

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour obtenir de l'aide :
1. Consultez la documentation dans `/docs`
2. Vérifiez les logs de l'application
3. Ouvrez une issue sur GitHub

## 🔄 Changelog

### v1.0.0
- Conversion MSG vers PDF
- Authentification JWT avec JWKS
- Fusion des pièces jointes PDF
- Tests unitaires complets
- Documentation complète