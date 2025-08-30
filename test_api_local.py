"""
Script de test local pour l'API MSG to PDF
"""
import requests
import time
import sys

def test_api():
    """Test de l'API en mode développement"""
    base_url = "http://localhost:8000"
    
    print("🧪 Test de l'API MSG to PDF en mode développement")
    print("=" * 60)
    
    # Attendre que l'API soit prête
    print("⏳ Attente du démarrage de l'API...")
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ API prête !")
                break
        except requests.exceptions.RequestException:
            time.sleep(1)
            print(f"   Tentative {i+1}/10...")
    else:
        print("❌ L'API ne répond pas. Vérifiez qu'elle est démarrée.")
        return False
    
    # Test 1: Health check
    print("\n1️⃣ Test de santé de l'API")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data['status']}")
            print(f"   📊 Version: {data['version']}")
            print(f"   🔑 JWKS: {data['jwks_status']}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 2: User info (sans authentification en mode dev)
    print("\n2️⃣ Test des informations utilisateur (mode dev)")
    try:
        response = requests.get(f"{base_url}/user/info")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ User ID: {data['user_id']}")
            print(f"   📧 Email: {data['email']}")
            print(f"   👥 Roles: {data['roles']}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 3: Conversion (avec un fichier de test)
    print("\n3️⃣ Test de conversion (fichier de test)")
    try:
        # Création d'un fichier de test simple
        test_content = b"Test MSG file content for API testing"
        files = {"file": ("test.msg", test_content, "application/octet-stream")}
        data = {"merge_attachments": "true"}
        
        response = requests.post(f"{base_url}/convert", files=files, data=data)
        
        if response.status_code == 200:
            print("   ✅ Conversion réussie !")
            print(f"   📄 Taille du PDF: {len(response.content)} bytes")
            print(f"   🆔 Request ID: {response.headers.get('X-Request-ID', 'N/A')}")
            print(f"   ⏱️ Temps de traitement: {response.headers.get('X-Processing-Time', 'N/A')}s")
            
            # Sauvegarde du PDF de test
            with open("test_output.pdf", "wb") as f:
                f.write(response.content)
            print("   💾 PDF sauvegardé dans 'test_output.pdf'")
            
        else:
            print(f"   ❌ Erreur de conversion: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📝 Détail: {error_data.get('detail', 'Erreur inconnue')}")
            except:
                print(f"   📝 Réponse: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Tous les tests sont passés avec succès !")
    print("\n📋 Résumé:")
    print("   • API de santé : ✅")
    print("   • Authentification (mode dev) : ✅")
    print("   • Conversion MSG vers PDF : ✅")
    print("\n🌐 Documentation disponible sur:")
    print("   • Swagger UI: http://localhost:8000/docs")
    print("   • ReDoc: http://localhost:8000/redoc")
    
    return True

def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python test_api_local.py")
        print("\nCe script teste l'API MSG to PDF en mode développement.")
        print("Assurez-vous que l'API est démarrée avec 'python run.py'")
        return
    
    success = test_api()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()