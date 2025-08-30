# 🧪 Guide de Test Local - API MSG to PDF

Ce guide vous explique comment tester l'API en local sans avoir de serveur JWT/JWKS.

## 🚀 Méthodes de Test

### Méthode 1 : Mode Développement (RECOMMANDÉ)

Le plus simple pour tester rapidement sans JWT.

#### 1. Configuration
```bash
# Copiez le fichier de configuration de développement
cp .env.dev .env
```

#### 2. Démarrage de l'API
```bash
python run.py
```

#### 3. Test sans authentification
```bash
# Test de santé
curl http://localhost:8000/health

# Test des informations utilisateur (sans token)
curl http://localhost:8000/user/info

# Test de conversion (sans token)
curl -X POST "http://localhost:8000/convert" \
     -F "file=@votre_fichier.msg" \
     -F "merge_attachments=true" \
     --output converted.pdf
```

### Méthode 2 : Avec JWT Généré

Pour tester avec un vrai JWT (plus proche de la production).

#### 1. Génération d'un JWT de test
```bash
cd dev_tools
python jwt_generator.py
```

Cela génère :
- Un token JWT valide
- Les clés JWKS correspondantes
- Sauvegarde dans `dev_jwt_token.txt` et `dev_jwks.json`

#### 2. Démarrage du serveur JWKS local
```bash
# Terminal 1 : Serveur JWKS
cd dev_tools
python jwks_server.py
```

#### 3. Configuration de l'API
```bash
# Créez un fichier .env avec :
JWKS_URL=http://localhost:8001/.well-known/jwks.json
JWT_AUDIENCE=dev-test-audience
JWT_ISSUER=dev-test-issuer
DISABLE_AUTH=false
```

#### 4. Démarrage de l'API
```bash
# Terminal 2 : API principale
python run.py
```

#### 5. Test avec JWT
```bash
# Récupérez le token depuis dev_jwt_token.txt
TOKEN=$(cat dev_tools/dev_jwt_token.txt)

# Test avec authentification
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/user/info

# Conversion avec authentification
curl -X POST "http://localhost:8000/convert" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@votre_fichier.msg" \
     -F "merge_attachments=true" \
     --output converted.pdf
```

## 📁 Création d'un fichier .msg de test

Si vous n'avez pas de fichier .msg, voici comment en créer un simple :

### Option 1 : Outlook
1. Ouvrez Outlook
2. Créez un nouvel email avec du contenu
3. Ajoutez éventuellement un PDF en pièce jointe
4. Sauvegardez comme fichier .msg

### Option 2 : Fichier de test minimal
```bash
# Créez un fichier de test (ne sera pas un vrai .msg mais pour tester l'API)
echo "Test MSG content" > test.msg
```

## 🔧 Variables d'Environnement

### Mode Développement
```env
DEV_MODE=true
DISABLE_AUTH=true
LOG_LEVEL=DEBUG
TEMP_DIR=./temp
```

### Mode Production avec JWT Local
```env
JWKS_URL=http://localhost:8001/.well-known/jwks.json
JWT_AUDIENCE=dev-test-audience
JWT_ISSUER=dev-test-issuer
DISABLE_AUTH=false
LOG_LEVEL=INFO
```

## 📊 Endpoints Disponibles

### 🏥 Santé de l'API
```http
GET /health
```
**Réponse :**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "jwks_status": "ok"
}
```

### 👤 Informations Utilisateur
```http
GET /user/info
Authorization: Bearer <token> (optionnel en mode dev)
```
**Réponse :**
```json
{
  "user_id": "dev-user-123",
  "email": "dev@example.com",
  "roles": ["user", "admin"]
}
```

### 🔄 Conversion MSG vers PDF
```http
POST /convert
Authorization: Bearer <token> (optionnel en mode dev)
Content-Type: multipart/form-data

file: <fichier.msg>
merge_attachments: true|false
```

## 🐛 Dépannage

### Erreur "Module not found"
```bash
pip install -r requirements.txt
```

### Erreur JWKS en mode production
- Vérifiez que le serveur JWKS local fonctionne sur le port 8001
- Vérifiez l'URL JWKS dans votre configuration

### Erreur de conversion MSG
- Vérifiez que le fichier est bien un .msg valide
- Vérifiez les permissions de lecture du fichier
- Consultez les logs pour plus de détails

### Port déjà utilisé
```bash
# Changez le port dans run.py ou utilisez :
uvicorn app.main:app --port 8080
```

## 📝 Exemples Complets

### Test Rapide (Mode Dev)
```bash
# 1. Configuration
cp .env.dev .env

# 2. Démarrage
python run.py

# 3. Test (dans un autre terminal)
curl http://localhost:8000/health
curl http://localhost:8000/user/info
```

### Test Complet avec JWT
```bash
# 1. Génération JWT
cd dev_tools && python jwt_generator.py

# 2. Serveur JWKS (terminal 1)
python jwks_server.py

# 3. Configuration API
echo "JWKS_URL=http://localhost:8001/.well-known/jwks.json" > .env
echo "DISABLE_AUTH=false" >> .env

# 4. API (terminal 2)
cd .. && python run.py

# 5. Test (terminal 3)
TOKEN=$(cat dev_tools/dev_jwt_token.txt)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/user/info
```

## 🎯 Documentation Interactive

Une fois l'API démarrée, accédez à :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

Vous pouvez tester directement les endpoints depuis l'interface Swagger !

## ✅ Checklist de Test

- [ ] API démarre sans erreur
- [ ] Endpoint `/health` répond
- [ ] Endpoint `/user/info` fonctionne
- [ ] Conversion d'un fichier .msg réussit
- [ ] PDF généré est valide
- [ ] Logs sont visibles et informatifs
- [ ] Documentation Swagger accessible