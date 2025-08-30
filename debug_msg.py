"""
Script de diagnostic pour analyser un fichier MSG
"""
import extract_msg
import sys
import os

def debug_msg_file(filename):
    """Analyse détaillée d'un fichier MSG"""
    
    if not os.path.exists(filename):
        print(f"❌ Fichier {filename} non trouvé")
        return
    
    print(f"🔍 Analyse du fichier: {filename}")
    print("=" * 60)
    
    try:
        # Ouvrir le fichier MSG
        msg = extract_msg.Message(filename)
        
        print(f"📧 Informations du message:")
        print(f"   De: {msg.sender}")
        print(f"   À: {msg.to}")
        print(f"   CC: {msg.cc}")
        print(f"   Objet: {msg.subject}")
        print(f"   Date: {msg.date}")
        print(f"   Taille du corps: {len(msg.body) if msg.body else 0} caractères")
        
        print(f"\n📎 Pièces jointes:")
        if msg.attachments:
            print(f"   Nombre total: {len(msg.attachments)}")
            
            for i, attachment in enumerate(msg.attachments):
                print(f"\n   📄 Pièce jointe {i+1}:")
                print(f"      Nom long: {attachment.longFilename}")
                print(f"      Nom court: {attachment.shortFilename}")
                print(f"      Taille: {len(attachment.data) if attachment.data else 0} bytes")
                print(f"      Type: {type(attachment.data)}")
                
                # Vérifier si c'est un PDF
                filename_to_check = attachment.longFilename or attachment.shortFilename or f"attachment_{i}"
                is_pdf = filename_to_check.lower().endswith('.pdf')
                print(f"      Nom pour vérification: '{filename_to_check}'")
                print(f"      Longueur du nom: {len(filename_to_check)}")
                print(f"      Bytes du nom: {filename_to_check.encode('utf-8')}")
                print(f"      Nom en minuscules: '{filename_to_check.lower()}'")
                print(f"      Se termine par .pdf: {is_pdf}")
                print(f"      Test direct: {'boarding-pass.pdf'.endswith('.pdf')}")
                
                if is_pdf and attachment.data:
                    # Vérifier le header PDF
                    header = attachment.data[:10] if len(attachment.data) >= 10 else attachment.data
                    is_valid_pdf = header.startswith(b'%PDF')
                    print(f"      Header PDF valide: {is_valid_pdf}")
                    print(f"      Header: {header}")
        else:
            print("   ❌ Aucune pièce jointe trouvée")
        
        msg.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    filename = "aaaa.msg" if len(sys.argv) < 2 else sys.argv[1]
    debug_msg_file(filename)