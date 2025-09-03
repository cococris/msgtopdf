#!/usr/bin/env python3
"""
Test de l'API complète avec le fichier CV.msg
"""
import sys
import os
import requests
import jwt
import datetime

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def create_test_jwt():
    """Crée un JWT de test simple pour les tests locaux"""
    payload = {
        'sub': 'test-user',
        'email': 'test@example.com',
        'roles': ['user'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        'iat': datetime.datetime.utcnow()
    }
    
    # Clé secrète simple pour les tests (ne pas utiliser en production !)
    secret = "test-secret-key-for-local-development-only"
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token

def test_api_conversion():
    """Test de l'API avec le fichier CV.msg"""
    print("🌐 Test de l'API complète avec CV.msg...")
    print("=" * 60)
    
    try:
        # Vérifier que le fichier existe
        cv_path = "CV.msg"
        if not os.path.exists(cv_path):
            print(f"❌ Fichier {cv_path} non trouvé!")
            return False
        
        print(f"📁 Fichier CV.msg trouvé ({os.path.getsize(cv_path)} bytes)")
        
        # Créer un token JWT pour le test
        try:
            token = create_test_jwt()
            print("✅ Token JWT de test créé")
        except Exception as e:
            print(f"⚠️ Impossible de créer le JWT: {e}")
            print("💡 Test sans authentification (peut échouer si l'auth est activée)")
            token = None
        
        # URL de l'API (supposons qu'elle tourne localement)
        api_url = "http://localhost:8000/convert"
        
        # Préparer les headers
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Préparer les données du formulaire
        files = {
            'file': ('CV.msg', open(cv_path, 'rb'), 'application/octet-stream')
        }
        data = {
            'merge_attachments': 'true',
            'strict_mode': 'false'
        }
        
        print("\n🚀 Envoi de la requête à l'API...")
        print(f"URL: {api_url}")
        print(f"Données: {data}")
        
        try:
            response = requests.post(api_url, files=files, data=data, headers=headers, timeout=30)
            
            print(f"📡 Statut de réponse: {response.status_code}")
            
            if response.status_code == 200:
                # Succès !
                pdf_content = response.content
                print(f"✅ Conversion réussie: {len(pdf_content)} bytes reçus")
                
                # Sauvegarder le PDF
                output_path = "api_converted_cv.pdf"
                with open(output_path, 'wb') as f:
                    f.write(pdf_content)
                print(f"✅ PDF sauvegardé: {output_path}")
                
                # Vérifier la validité du PDF
                from PyPDF2 import PdfReader
                from io import BytesIO
                try:
                    reader = PdfReader(BytesIO(pdf_content))
                    print(f"✅ PDF valide avec {len(reader.pages)} page(s)")
                    
                    # Vérifier les headers de réponse
                    print("\n📋 Headers de réponse:")
                    interesting_headers = [
                        'Content-Disposition', 'X-Request-ID', 'X-Processing-Time',
                        'X-Attachments-Processed', 'X-Original-Size', 'X-Output-Size'
                    ]
                    for header in interesting_headers:
                        if header in response.headers:
                            print(f"  {header}: {response.headers[header]}")
                    
                    return True
                    
                except Exception as pdf_e:
                    print(f"❌ PDF reçu invalide: {pdf_e}")
                    return False
                    
            elif response.status_code == 401:
                print("❌ Erreur d'authentification (401)")
                print("💡 L'API nécessite une authentification JWT valide")
                print("📄 Réponse:", response.text[:200])
                return False
                
            elif response.status_code == 400:
                print("❌ Erreur de requête (400)")
                print("📄 Réponse:", response.text)
                return False
                
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                print("📄 Réponse:", response.text[:500])
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Impossible de se connecter à l'API")
            print("💡 Assurez-vous que l'API est démarrée sur http://localhost:8000")
            print("💡 Vous pouvez démarrer l'API avec: python -m app.main")
            return False
            
        except requests.exceptions.Timeout:
            print("❌ Timeout de la requête")
            print("💡 La conversion peut prendre du temps, augmentez le timeout")
            return False
            
        finally:
            # Fermer le fichier
            if 'file' in files:
                files['file'][1].close()
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_conversion():
    """Test de conversion directe (sans API)"""
    print("\n🔧 Test de conversion directe (sans API)...")
    print("-" * 40)
    
    try:
        from app.services.msg_converter import MSGConverter
        
        cv_path = "CV.msg"
        converter = MSGConverter()
        
        # Conversion directe
        main_pdf, attachment_pdfs = converter.convert_msg_to_pdf(cv_path, "direct-test")
        
        # Fusion
        if attachment_pdfs:
            final_pdf = converter.merge_pdfs(main_pdf, attachment_pdfs, "direct-test")
        else:
            final_pdf = main_pdf
        
        print(f"✅ Conversion directe réussie: {len(final_pdf)} bytes")
        
        # Sauvegarder
        with open("direct_converted_cv.pdf", "wb") as f:
            f.write(final_pdf)
        print("✅ PDF sauvegardé: direct_converted_cv.pdf")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion directe: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test complet de l'API avec CV.msg...")
    print("=" * 60)
    
    # Test de conversion directe (devrait toujours marcher)
    direct_success = test_direct_conversion()
    
    # Test de l'API (peut échouer si l'API n'est pas démarrée)
    api_success = test_api_conversion()
    
    print("=" * 60)
    print("📊 Résultats des tests:")
    print(f"  Conversion directe: {'✅ Succès' if direct_success else '❌ Échec'}")
    print(f"  API: {'✅ Succès' if api_success else '❌ Échec'}")
    
    if direct_success:
        print("\n💡 La conversion fonctionne parfaitement !")
        print("💡 Vérifiez les fichiers PDF générés:")
        print("   - direct_converted_cv.pdf")
        if api_success:
            print("   - api_converted_cv.pdf")
    
    if not api_success:
        print("\n💡 Si l'API a échoué, démarrez-la avec:")
        print("   python -m app.main")
        print("   puis relancez ce test")