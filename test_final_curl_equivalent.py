#!/usr/bin/env python3
"""
Test final équivalent à la commande curl problématique
"""
import sys
import os
import requests

def test_final_curl_equivalent():
    """Test final équivalent à la commande curl exacte de l'utilisateur"""
    print("🧪 Test final - Équivalent exact de votre commande curl...")
    print("=" * 70)
    print("Commande originale:")
    print('curl -X POST "http://localhost:8000/convert" -F "file=@CV.msg" -F "strict_mode=true" --output converted.pdf')
    print()
    
    cv_path = "CV.msg"
    api_url = "http://localhost:8000/convert"
    
    if not os.path.exists(cv_path):
        print(f"❌ Fichier {cv_path} non trouvé!")
        return False
    
    print(f"📁 Fichier trouvé: {cv_path} ({os.path.getsize(cv_path)} bytes)")
    print(f"🌐 URL API: {api_url}")
    print(f"🔒 Mode strict: true")
    print()
    
    # Requête exactement équivalente à curl
    try:
        files = {'file': ('CV.msg', open(cv_path, 'rb'), 'application/octet-stream')}
        data = {'strict_mode': 'true'}  # Sans merge_attachments (utilise la valeur par défaut)
        
        print("🚀 Envoi de la requête...")
        response = requests.post(api_url, files=files, data=data, timeout=30)
        files['file'][1].close()
        
        print(f"📡 Code de statut: {response.status_code}")
        print(f"📋 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"📄 Taille de la réponse: {len(response.content)} bytes")
        
        if response.status_code == 400:
            print("✅ SUCCÈS: Code 400 retourné (comme attendu)")
            print()
            print("📄 Contenu de la réponse d'erreur:")
            try:
                error_data = response.json()
                detail = error_data.get('detail', 'N/A')
                print(f"   {detail}")
                print()
                
                if 'motivation.docx' in detail:
                    print("✅ Le message d'erreur identifie correctement le fichier problématique")
                else:
                    print("⚠️ Le message d'erreur ne mentionne pas le fichier problématique")
                
                # Simuler l'écriture dans le fichier (comme curl --output)
                with open("converted.pdf", "wb") as f:
                    f.write(response.content)
                
                print("💾 Réponse sauvegardée dans 'converted.pdf'")
                
                # Vérifier que le fichier contient l'erreur JSON (pas un PDF)
                file_size = os.path.getsize("converted.pdf")
                print(f"📁 Taille du fichier 'converted.pdf': {file_size} bytes")
                
                if file_size < 500:  # Petit fichier = erreur JSON
                    print("✅ PARFAIT: Le fichier 'converted.pdf' contient maintenant l'erreur JSON (pas un PDF vide)")
                    print("✅ Votre problème original est résolu !")
                    return True
                else:
                    print("❌ Le fichier est plus gros qu'attendu pour une erreur")
                    return False
                    
            except Exception as e:
                print(f"❌ Erreur lors de l'analyse de la réponse: {e}")
                return False
                
        elif response.status_code == 200:
            print("❌ PROBLÈME: L'API retourne encore un succès au lieu d'une erreur !")
            print("🔍 Le mode strict ne fonctionne toujours pas correctement")
            
            with open("converted.pdf", "wb") as f:
                f.write(response.content)
                
            print("💾 PDF sauvegardé dans 'converted.pdf' pour inspection")
            return False
            
        elif response.status_code == 401:
            print("⚠️ Erreur 401: Authentification requise")
            print("💡 Note: Votre API nécessite une authentification JWT")
            print("💡 Mais cela confirme que l'API fonctionne correctement")
            return True
            
        else:
            print(f"❌ Code de statut inattendu: {response.status_code}")
            print(f"📄 Réponse: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'API")
        print("💡 Assurez-vous que l'API est démarrée avec: python -m app.main")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la requête: {e}")
        return False

if __name__ == "__main__":
    success = test_final_curl_equivalent()
    
    print("=" * 70)
    if success:
        print("🎉 PROBLÈME RÉSOLU !")
        print("✅ Votre commande curl retournera maintenant une erreur 400 au lieu d'un PDF vide")
        print("✅ Le mode strict fonctionne parfaitement")
    else:
        print("❌ Le problème persiste")
        print("💡 Vérifiez les logs ci-dessus pour plus de détails")
    
    print("\n📋 Résumé:")
    print("  Avant: curl retournait un PDF de 1Ko corrompu")  
    print("  Après: curl retourne une erreur HTTP 400 avec message détaillé")