#!/usr/bin/env python3
"""
Test de stress spécialisé pour 50 conversions simultanées du CV.msg
"""
import os
import time
import random
import jwt
from datetime import datetime, timedelta
from locust import HttpUser, task, between
from io import BytesIO

class CVStressTestUser(HttpUser):
    """Utilisateur spécialisé pour test de stress avec CV.msg uniquement"""
    
    wait_time = between(0.1, 0.5)  # Attente très courte pour stress test
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.jwt_token = None
        self.cv_data = None
        self.conversion_count = 0
        self.start_time = None
    
    def on_start(self):
        """Initialisation lors du démarrage d'un utilisateur"""
        self.start_time = time.time()
        
        # Générer un token JWT de test
        self.jwt_token = self._create_test_jwt()
        
        # Charger le fichier CV.msg
        if not self._load_cv_file():
            print(f"❌ ERREUR: Impossible de charger CV.msg - Arrêt de l'utilisateur")
            self.environment.runner.quit()
            return
        
        user_id = random.randint(1, 1000)
        print(f"🚀 Utilisateur CV-{user_id:03d} prêt pour test de stress")
    
    def _create_test_jwt(self):
        """Crée un JWT de test valide"""
        user_id = random.randint(1000, 9999)
        payload = {
            'sub': f'cv-stress-user-{user_id}',
            'email': f'stress-test-{user_id}@loadtest.com',
            'roles': ['user'],
            'exp': datetime.now() + timedelta(hours=1),
            'iat': datetime.now()
        }
        
        secret = "test-secret-key-for-local-development-only"
        token = jwt.encode(payload, secret, algorithm='HS256')
        return token
    
    def _load_cv_file(self):
        """Charge le fichier CV.msg"""
        cv_path = "CV.msg"
        if not os.path.exists(cv_path):
            print(f"❌ Fichier {cv_path} non trouvé!")
            return False
        
        try:
            with open(cv_path, "rb") as f:
                self.cv_data = f.read()
            
            file_size = len(self.cv_data)
            print(f"✅ CV.msg chargé: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du chargement de CV.msg: {e}")
            return False
    
    def _get_auth_headers(self):
        """Retourne les headers d'authentification"""
        if self.jwt_token:
            return {"Authorization": f"Bearer {self.jwt_token}"}
        return {}
    
    @task(10)  # Tâche principale - conversion CV
    def convert_cv_normal(self):
        """Conversion CV.msg en mode normal"""
        self.conversion_count += 1
        
        files = {
            "file": (f"CV-test-{self.conversion_count}.msg", BytesIO(self.cv_data), "application/octet-stream")
        }
        data = {
            "merge_attachments": "true",
            "strict_mode": "false"
        }
        
        start_request_time = time.time()
        
        with self.client.post(
            "/convert",
            files=files,
            data=data,
            headers=self._get_auth_headers(),
            timeout=120,  # Timeout généreux pour CV volumineux
            catch_response=True,
            name="CV_conversion_normal"
        ) as response:
            request_time = time.time() - start_request_time
            
            if response.status_code == 200:
                pdf_size = len(response.content)
                if pdf_size > 100000:  # PDF CV devrait être > 100KB
                    response.success()
                    print(f"✅ Conversion #{self.conversion_count} réussie: {pdf_size:,} bytes en {request_time:.2f}s")
                else:
                    response.failure(f"PDF trop petit: {pdf_size} bytes")
                    
            elif response.status_code == 422:
                # Erreur de conversion - peut arriver sous forte charge
                response.failure(f"Erreur de conversion: {response.text[:100]}")
                
            elif response.status_code == 500:
                # Erreur serveur - problématique sous charge
                response.failure(f"Erreur serveur 500: {response.text[:100]}")
                
            elif response.status_code == 401:
                response.failure("Erreur d'authentification JWT")
                
            else:
                response.failure(f"Code HTTP inattendu: {response.status_code}")
    
    @task(3)  # Test en mode strict (devrait échouer à cause du .docx)
    def convert_cv_strict(self):
        """Conversion CV.msg en mode strict (test d'erreur 400)"""
        files = {
            "file": (f"CV-strict-{self.conversion_count}.msg", BytesIO(self.cv_data), "application/octet-stream")
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
            timeout=60,
            catch_response=True,
            name="CV_conversion_strict"
        ) as response:
            if response.status_code == 400:
                # Comportement attendu (motivation.docx non autorisé)
                response.success()
                
            elif response.status_code == 200:
                response.failure("Mode strict n'a pas rejeté le fichier .docx!")
                
            elif response.status_code in [422, 500]:
                response.failure(f"Erreur serveur en mode strict: {response.status_code}")
                
            else:
                response.failure(f"Code inattendu en mode strict: {response.status_code}")
    
    @task(1)  # Health check occasionnel
    def health_check(self):
        """Vérification de santé pendant le stress test"""
        with self.client.get("/health", timeout=10, catch_response=True, name="health_during_stress") as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure(f"API pas healthy: {data}")
                except:
                    response.failure("Health check réponse JSON invalide")
            else:
                response.failure(f"Health check échoué: {response.status_code}")
    
    def on_stop(self):
        """Statistiques finales à l'arrêt"""
        total_time = time.time() - self.start_time if self.start_time else 0
        print(f"🏁 Utilisateur terminé: {self.conversion_count} conversions en {total_time:.1f}s")


if __name__ == "__main__":
    print("""
🔥 Test de Stress CV.msg - 50 Conversions Simultanées
====================================================

Ce test va lancer 50 utilisateurs simultanés convertissant le fichier CV.msg.

Commande de test:
locust -f locust_cv_stress_test.py --host=http://localhost:8000 --users=50 --spawn-rate=10 --run-time=2m --headless

Métriques importantes à surveiller:
- Taux de succès (objectif: > 90%)
- Temps de réponse moyen (objectif: < 5s)
- Erreurs 500 (objectif: 0%)
- Utilisation CPU/Mémoire serveur

ATTENTION: Ce test est intensif - surveiller les ressources système !
""")