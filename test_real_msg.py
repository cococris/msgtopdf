"""
Test avec un vrai fichier MSG
"""
import requests
import os

def test_real_msg_file():
    """Test avec le fichier aaaa.msg"""
    
    # Vérifier que le fichier existe
    if not os.path.exists("aaaa.msg"):
        print("❌ Fichier aaaa.msg non trouvé")
        return
    
    print("🧪 Test avec le fichier MSG réel: aaaa.msg")
    print("=" * 50)
    
    # Préparer la requête
    url = "http://localhost:8000/convert"
    
    with open("aaaa.msg", "rb") as f:
        files = {"file": ("aaaa.msg", f, "application/octet-stream")}
        data = {"merge_attachments": "true"}
        
        print("📤 Envoi de la requête...")
        try:
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📋 Headers:")
            for key, value in response.headers.items():
                if key.startswith('X-'):
                    print(f"   {key}: {value}")
            
            if response.status_code == 200:
                # Sauvegarder le PDF
                with open("aaaa_converted.pdf", "wb") as pdf_file:
                    pdf_file.write(response.content)
                
                print(f"✅ Conversion réussie!")
                print(f"📄 PDF sauvegardé: aaaa_converted.pdf ({len(response.content)} bytes)")
                print(f"📎 Pièces jointes traitées: {response.headers.get('X-Attachments-Processed', '0')}")
                
            else:
                print(f"❌ Erreur: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"📝 Détail: {error_data.get('detail', 'Erreur inconnue')}")
                except:
                    print(f"📝 Réponse: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"❌ Erreur de requête: {e}")

if __name__ == "__main__":
    test_real_msg_file()