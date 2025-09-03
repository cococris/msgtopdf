#!/usr/bin/env python3
"""
Test de charge Locust pour l'API MSG to PDF
"""
import os
import time
import random
import jwt
from datetime import datetime, timedelta
from locust import HttpUser, task, between
from io import BytesIO

class MSGToPDFUser(HttpUser):
    """Utilisateur simulé pour les tests de charge de l'API MSG to PDF"""
    
    wait_time = between(1, 3)  # Attendre 1-3 secondes entre les requêtes
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.jwt_token = None
        self.test_files = {}
        self.request_count = 0
    
    def on_start(self):
        """Initialisation lors du démarrage d'un utilisateur"""
        # Générer un token JWT de test
        self.jwt_token = self._create_test_jwt()
        
        # Préparer les fichiers de test
        self._prepare_test_files()
        
        print(f"👤 Utilisateur {self.client.base_url} démarré avec token JWT")
    
    def _create_test_jwt(self):
        """Crée un JWT de test valide"""
        payload = {
            'sub': f'load-test-user-{random.randint(1000, 9999)}',
            'email': f'test-{random.randint(100, 999)}@loadtest.com',
            'roles': ['user'],
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        # Clé secrète simple pour les tests (cohérente avec les autres tests)
        secret = "test-secret-key-for-local-development-only"
        token = jwt.encode(payload, secret, algorithm='HS256')
        return token
    
    def _prepare_test_files(self):
        """Prépare les fichiers de test"""
        # Si CV.msg existe, l'utiliser
        if os.path.exists("CV.msg"):
            with open("CV.msg", "rb") as f:
                self.test_files["cv"] = f.read()
        
        # Créer des fichiers MSG simulés de différentes tailles
        self.test_files["small"] = self._create_mock_msg_data(1024)      # 1KB
        self.test_files["medium"] = self._create_mock_msg_data(10240)    # 10KB
        self.test_files["large"] = self._create_mock_msg_data(102400)    # 100KB
    
    def _create_mock_msg_data(self, size):
        """Crée des données MSG simulées pour les tests"""
        # En réalité, on simule juste avec des données binaires
        # car créer un vrai fichier MSG est complexe
        return b"MOCK_MSG_DATA" * (size // 13)
    
    def _get_auth_headers(self):
        """Retourne les headers d'authentification"""
        if self.jwt_token:
            return {"Authorization": f"Bearer {self.jwt_token}"}
        return {}
    
    @task(5)  # Poids 5 - tâche principale
    def convert_msg_normal_mode(self):
        """Test de conversion normale (mode le plus fréquent)"""
        self.request_count += 1
        
        # Choisir un fichier de test aléatoire
        file_key = random.choice(["small", "medium"])
        if "cv" in self.test_files:
            file_key = random.choice(["cv", "small", "medium"])
        
        file_data = self.test_files[file_key]
        
        files = {
            "file": (f"test-{file_key}.msg", BytesIO(file_data), "application/octet-stream")
        }
        data = {
            "merge_attachments": "true",
            "strict_mode": "false"
        }
        
        with self.client.post(
            "/convert",
            files=files,
            data=data,
            headers=self._get_auth_headers(),
            timeout=30,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                # Vérifier que c'est bien un PDF
                if len(response.content) > 1000:  # PDF devrait être > 1KB
                    response.success()
                else:
                    response.failure(f"PDF trop petit: {len(response.content)} bytes")
            elif response.status_code == 422:
                # Erreur de conversion normale (fichier mock invalide)
                response.success()  # C'est acceptable pour un fichier mock
            elif response.status_code == 401:
                response.failure("Erreur d'authentification")
            else:
                response.failure(f"Code inattendu: {response.status_code}")
    
    @task(2)  # Poids 2 - mode strict
    def convert_msg_strict_mode(self):
        """Test de conversion en mode strict"""
        file_key = random.choice(["small", "medium"])
        file_data = self.test_files[file_key]
        
        files = {
            "file": (f"test-strict-{file_key}.msg", BytesIO(file_data), "application/octet-stream")
        }
        data = {
            "merge_attachments": "true",
            "strict_mode": "true"
        }
        
        with self.client.post(
            "/convert",
            files=files,
            data=data,
            headers=self._get_auth_headers(),
            timeout=30,
            catch_response=True
        ) as response:
            if response.status_code in [200, 400, 422]:
                response.success()  # Tous ces codes sont acceptables
            elif response.status_code == 401:
                response.failure("Erreur d'authentification")
            else:
                response.failure(f"Code inattendu: {response.status_code}")
    
    @task(1)  # Poids 1 - fichier volumineux
    def convert_large_file(self):
        """Test avec fichier volumineux"""
        if "cv" in self.test_files:
            file_data = self.test_files["cv"]  # Utiliser le vrai CV.msg
        else:
            file_data = self.test_files["large"]
        
        files = {
            "file": ("large-test.msg", BytesIO(file_data), "application/octet-stream")
        }
        data = {
            "merge_attachments": "true",
            "strict_mode": "false"
        }
        
        with self.client.post(
            "/convert",
            files=files,
            data=data,
            headers=self._get_auth_headers(),
            timeout=60,  # Timeout plus long pour les gros fichiers
            catch_response=True
        ) as response:
            if response.status_code in [200, 422]:
                response.success()
            elif response.status_code == 413:
                response.success()  # Fichier trop gros - acceptable
            elif response.status_code == 401:
                response.failure("Erreur d'authentification")
            else:
                response.failure(f"Code inattendu: {response.status_code}")
    
    @task(3)  # Poids 3 - endpoint de santé
    def health_check(self):
        """Test de l'endpoint de santé"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure("API pas en bonne santé")
                except:
                    response.failure("Réponse JSON invalide")
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(1)  # Poids 1 - test d'authentification
    def user_info_check(self):
        """Test de l'endpoint d'informations utilisateur"""
        with self.client.get("/user/info", headers=self._get_auth_headers(), catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "user_id" in data:
                        response.success()
                    else:
                        response.failure("Données utilisateur invalides")
                except:
                    response.failure("Réponse JSON invalide")
            elif response.status_code == 401:
                response.failure("Token JWT invalide")
            else:
                response.failure(f"Code inattendu: {response.status_code}")
    
    @task(1)  # Poids 1 - test d'erreur
    def test_invalid_file(self):
        """Test avec fichier invalide pour tester la gestion d'erreurs"""
        fake_file_data = b"This is not a MSG file content"
        
        files = {
            "file": ("fake.msg", BytesIO(fake_file_data), "application/octet-stream")
        }
        data = {
            "merge_attachments": "false"
        }
        
        with self.client.post(
            "/convert",
            files=files,
            data=data,
            headers=self._get_auth_headers(),
            timeout=30,
            catch_response=True
        ) as response:
            if response.status_code in [400, 422]:
                response.success()  # Erreur attendue pour fichier invalide
            elif response.status_code == 401:
                response.failure("Erreur d'authentification")
            else:
                response.failure(f"Code inattendu pour fichier invalide: {response.status_code}")
    
    def on_stop(self):
        """Nettoyage lors de l'arrêt d'un utilisateur"""
        print(f"👋 Utilisateur terminé après {self.request_count} requêtes")


# Classes pour différents scénarios de test

class LightLoadUser(MSGToPDFUser):
    """Utilisateur pour charge légère - simule utilisation normale"""
    wait_time = between(2, 5)
    weight = 3

class HeavyLoadUser(MSGToPDFUser):
    """Utilisateur pour charge lourde - simule pics d'activité"""
    wait_time = between(0.5, 1.5)
    weight = 1
    
    @task(10)  # Plus de conversions
    def intensive_conversion(self):
        """Conversions intensives"""
        return self.convert_msg_normal_mode()

class StressTestUser(MSGToPDFUser):
    """Utilisateur pour tests de stress"""
    wait_time = between(0.1, 0.5)
    weight = 1
    
    @task(15)
    def stress_conversion(self):
        """Conversions de stress"""
        return self.convert_msg_normal_mode()


if __name__ == "__main__":
    print("""
🐝 Locust Load Testing pour API MSG to PDF
==========================================

Commandes de test disponibles :

1. Test léger (10 utilisateurs, montée graduelle) :
   locust -f locustfile.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=2m

2. Test modéré (50 utilisateurs, 5 minutes) :
   locust -f locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=5m

3. Test de stress (100 utilisateurs, rapide) :
   locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=3m

4. Interface web (recommandé) :
   locust -f locustfile.py --host=http://localhost:8000
   Puis ouvrir : http://localhost:8089

Scénarios de test inclus :
✅ Conversion normale (poids 5)
✅ Mode strict (poids 2) 
✅ Fichiers volumineux (poids 1)
✅ Health checks (poids 3)
✅ Tests d'authentification (poids 1)
✅ Gestion d'erreurs (poids 1)
""")