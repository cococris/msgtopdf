#!/usr/bin/env python3
"""
Test spécifique du mode strict via l'API
"""
import sys
import os
import requests
import jwt
import datetime
import json

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def create_test_jwt():
    """Crée un JWT de test simple"""
    payload = {
        'sub': 'test-user',
        'email': 'test@example.com',
        'roles': ['user'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        'iat': datetime.datetime.utcnow()
    }
    
    secret = "test-secret-key-for-local-development-only"
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token

def test_strict_mode_behavior():
    """Test du comportement exact du mode strict"""
    print("🔒 Test du mode strict avec CV.msg (contient .docx non autorisé)...")
    print("=" * 70)
    
    cv_path = "CV.msg"
    if not os.path.exists(cv_path):
        print(f"❌ Fichier {cv_path} non trouvé!")
        return False
    
    # Rappel du contenu du CV.msg
    print("📋 Contenu du CV.msg:")
    print("  - CV_Corentin_FR.pdf (210KB) ✅ Autorisé")
    print("  - motivation.docx (13KB) ❌ Non autorisé")
    print("  → En mode strict, cela DOIT échouer avec erreur 400\n")
    
    api_url = "http://localhost:8000/convert"
    token = create_test_jwt()
    
    # Test 1: Mode normal (devrait réussir)
    print("🔍 Test 1: Mode normal (strict_mode=false)")
    print("-" * 50)
    
    headers = {'Authorization': f'Bearer {token}'}
    files = {'file': ('CV.msg', open(cv_path, 'rb'), 'application/octet-stream')}
    data = {'merge_attachments': 'true', 'strict_mode': 'false'}
    
    try:
        response = requests.post(api_url, files=files, data=data, headers=headers, timeout=30)
        files['file'][1].close()
        
        print(f"📡 Statut: {response.status_code}")
        print(f"📄 Taille réponse: {len(response.content)} bytes")
        print(f"📋 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            print("✅ Mode normal: Succès (attendu)")
            if len(response.content) > 50000:
                print("✅ PDF de taille cohérente reçu")
            else:
                print("⚠️ PDF reçu plus petit qu'attendu")
        else:
            print(f"❌ Mode normal: Erreur inattendue {response.status_code}")
            print(f"📄 Message: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test mode normal: {e}")
        return False
    
    print()
    
    # Test 2: Mode strict (devrait échouer avec 400)
    print("🔍 Test 2: Mode strict (strict_mode=true)")
    print("-" * 50)
    
    files = {'file': ('CV.msg', open(cv_path, 'rb'), 'application/octet-stream')}
    data = {'merge_attachments': 'true', 'strict_mode': 'true'}
    
    try:
        response = requests.post(api_url, files=files, data=data, headers=headers, timeout=30)
        files['file'][1].close()
        
        print(f"📡 Statut: {response.status_code}")
        print(f"📄 Taille réponse: {len(response.content)} bytes")
        print(f"📋 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 400:
            print("✅ Mode strict: Erreur 400 (attendu)")
            try:
                error_data = response.json()
                print(f"📄 Message d'erreur: {error_data.get('detail', 'N/A')}")
                
                # Vérifier que le message contient les bons éléments
                detail = error_data.get('detail', '')
                if 'motivation.docx' in detail and 'non autorisées' in detail:
                    print("✅ Message d'erreur correct et détaillé")
                    return True
                else:
                    print("⚠️ Message d'erreur ne contient pas les détails attendus")
                    
            except json.JSONDecodeError:
                print("❌ Réponse n'est pas du JSON valide")
                print(f"📄 Contenu brut: {response.text[:200]}")
                
        elif response.status_code == 200:
            print("❌ Mode strict: Succès inattendu (devrait échouer !)")
            print("🔍 Cela indique un bug dans la validation stricte")
            
            # Sauvegarder pour inspection
            with open("unexpected_strict_success.pdf", "wb") as f:
                f.write(response.content)
            print("💾 PDF inattendu sauvegardé: unexpected_strict_success.pdf")
            return False
            
        else:
            print(f"❌ Mode strict: Code de statut inattendu {response.status_code}")
            print(f"📄 Message: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test mode strict: {e}")
        return False
    
    return False

def test_curl_equivalent():
    """Test équivalent à la commande curl de l'utilisateur"""
    print("\n🖥️ Test équivalent à votre commande curl...")
    print("-" * 70)
    
    cv_path = "CV.msg"
    api_url = "http://localhost:8000/convert"
    
    # Commande curl simulée (sans authentification comme dans l'exemple de l'utilisateur)
    print("🔍 Simulation de: curl -X POST http://localhost:8000/convert -F 'file=@CV.msg' -F 'strict_mode=true'")
    print()
    
    files = {'file': ('CV.msg', open(cv_path, 'rb'), 'application/octet-stream')}
    data = {'strict_mode': 'true'}  # Sans merge_attachments (défaut), sans auth
    
    try:
        response = requests.post(api_url, files=files, data=data, timeout=30)
        files['file'][1].close()
        
        print(f"📡 Code de statut: {response.status_code}")
        print(f"📄 Taille de la réponse: {len(response.content)} bytes")
        print(f"📋 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 401:
            print("✅ Erreur d'authentification (attendu sans token)")
            print("💡 L'API nécessite une authentification JWT")
            return True
            
        elif response.status_code == 400:
            print("✅ Erreur 400: Pièces jointes non autorisées (attendu)")
            try:
                error_data = response.json()
                print(f"📄 Détail: {error_data.get('detail', 'N/A')}")
                return True
            except:
                print("📄 Réponse non-JSON")
                print(f"Contenu: {response.text[:200]}")
                
        elif response.status_code == 200:
            print("❌ PROBLÈME: L'API retourne un succès au lieu d'une erreur!")
            print("🔍 Cela explique pourquoi curl reçoit un PDF au lieu d'une erreur")
            
            # Sauvegarder pour analyse
            with open("curl_equivalent_result.pdf", "wb") as f:
                f.write(response.content)
            print("💾 Résultat sauvegardé: curl_equivalent_result.pdf")
            
            # Vérifier si c'est un PDF vide ou valide
            if len(response.content) < 1000:
                print("⚠️ PDF très petit (probablement vide/corrompu)")
            else:
                print("⚠️ PDF de taille normale (le mode strict ne fonctionne pas)")
            
            return False
            
        else:
            print(f"❌ Code de statut inattendu: {response.status_code}")
            print(f"📄 Réponse: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'API")
        print("💡 Démarrez l'API avec: python -m app.main")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("🔒 Test complet du mode strict API...")
    print("=" * 70)
    
    # Test avec authentification
    auth_success = test_strict_mode_behavior()
    
    # Test sans authentification (comme la commande curl de l'utilisateur)
    curl_success = test_curl_equivalent()
    
    print("=" * 70)
    print("📊 Résultats:")
    print(f"  Mode strict avec auth: {'✅ OK' if auth_success else '❌ Problème'}")
    print(f"  Curl équivalent: {'✅ OK' if curl_success else '❌ Problème'}")
    
    if not auth_success and not curl_success:
        print("\n🔍 DIAGNOSTIC:")
        print("  Le mode strict ne semble pas fonctionner correctement")
        print("  L'API retourne un PDF au lieu d'une erreur 400")
        print("  → Vérification du code nécessaire")