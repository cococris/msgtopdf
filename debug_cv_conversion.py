#!/usr/bin/env python3
"""
Script de debug pour le fichier CV.msg réel
"""
import sys
import os
from io import BytesIO
import traceback

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def debug_cv_msg():
    """Debug détaillé du fichier CV.msg"""
    print("🔍 Debug du fichier CV.msg...")
    print("=" * 60)
    
    try:
        from app.services.msg_converter import MSGConverter
        import extract_msg
        
        # Vérifier que le fichier existe
        cv_path = "CV.msg"
        if not os.path.exists(cv_path):
            print(f"❌ Fichier {cv_path} non trouvé!")
            return False
        
        file_size = os.path.getsize(cv_path)
        print(f"📁 Fichier trouvé: {cv_path} ({file_size} bytes)")
        
        # Étape 1: Tester l'ouverture du fichier MSG
        print("\n🔍 Étape 1: Ouverture du fichier MSG...")
        try:
            msg = extract_msg.Message(cv_path)
            print("✅ Fichier MSG ouvert avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture du MSG: {e}")
            return False
        
        # Étape 2: Examiner le contenu du message
        print("\n🔍 Étape 2: Analyse du contenu...")
        try:
            print(f"De: {msg.sender}")
            print(f"À: {msg.to}")
            print(f"CC: {msg.cc}")
            print(f"Objet: {msg.subject}")
            print(f"Date: {msg.date}")
            print(f"Corps: {len(msg.body) if msg.body else 0} caractères")
            print(f"Pièces jointes: {len(msg.attachments) if msg.attachments else 0}")
            
            if msg.attachments:
                for i, att in enumerate(msg.attachments):
                    filename = att.longFilename or att.shortFilename or f"attachment_{i}"
                    size = len(att.data) if att.data else 0
                    print(f"  - Pièce jointe {i+1}: {filename} ({size} bytes)")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'analyse du contenu: {e}")
        
        # Étape 3: Tester la création du convertisseur
        print("\n🔍 Étape 3: Initialisation du convertisseur...")
        try:
            converter = MSGConverter()
            print("✅ Convertisseur initialisé")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            traceback.print_exc()
            return False
        
        # Étape 4: Tester le nettoyage du contenu
        print("\n🔍 Étape 4: Test du nettoyage du contenu...")
        try:
            if msg.body:
                cleaned = converter._clean_content(msg.body)
                print(f"✅ Contenu nettoyé: {len(cleaned)} caractères")
                if len(cleaned) > 100:
                    print(f"Aperçu: {cleaned[:100]}...")
            else:
                print("⚠️ Pas de corps de message")
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage: {e}")
            traceback.print_exc()
        
        # Étape 5: Tester la création des styles
        print("\n🔍 Étape 5: Test des styles...")
        try:
            # Tester chaque style individuellement
            styles_to_test = [
                'title_style', 'header_style', 'meta_label_style', 
                'meta_value_style', 'body_style', 'paragraph_style'
            ]
            for style_name in styles_to_test:
                style = getattr(converter, style_name, None)
                if style:
                    print(f"✅ Style {style_name} OK")
                else:
                    print(f"❌ Style {style_name} manquant")
        except Exception as e:
            print(f"❌ Erreur avec les styles: {e}")
            traceback.print_exc()
        
        # Étape 6: Test de génération PDF simple
        print("\n🔍 Étape 6: Test de génération PDF basique...")
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            # Test avec contenu minimal
            story.append(Paragraph("Test basique", converter.title_style))
            
            doc.build(story)
            buffer.seek(0)
            test_pdf = buffer.getvalue()
            
            if len(test_pdf) > 100:
                print(f"✅ PDF basique créé: {len(test_pdf)} bytes")
                
                # Sauvegarder pour test
                with open("debug_basic_test.pdf", "wb") as f:
                    f.write(test_pdf)
                print("✅ PDF de test basique sauvegardé: debug_basic_test.pdf")
            else:
                print(f"❌ PDF basique trop petit: {len(test_pdf)} bytes")
                
        except Exception as e:
            print(f"❌ Erreur lors de la génération PDF basique: {e}")
            traceback.print_exc()
        
        # Étape 7: Test avec le contenu réel (mais version simplifiée)
        print("\n🔍 Étape 7: Test avec contenu réel simplifié...")
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            # Version très simple du contenu
            story.append(Paragraph("Email Outlook", converter.title_style))
            
            if msg.sender:
                story.append(Paragraph(f"De: {msg.sender}", converter.meta_value_style))
            if msg.subject:
                story.append(Paragraph(f"Objet: {msg.subject}", converter.meta_value_style))
            
            if msg.body and len(msg.body) < 1000:  # Limiter la taille pour le test
                safe_body = msg.body.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')[:500]
                story.append(Paragraph(f"Contenu: {safe_body}", converter.paragraph_style))
            
            doc.build(story)
            buffer.seek(0)
            simple_pdf = buffer.getvalue()
            
            if len(simple_pdf) > 100:
                print(f"✅ PDF simplifié créé: {len(simple_pdf)} bytes")
                
                with open("debug_simplified_cv.pdf", "wb") as f:
                    f.write(simple_pdf)
                print("✅ PDF simplifié sauvegardé: debug_simplified_cv.pdf")
                
                # Test d'ouverture
                from PyPDF2 import PdfReader
                try:
                    reader = PdfReader(BytesIO(simple_pdf))
                    print(f"✅ PDF simplifié valide avec {len(reader.pages)} page(s)")
                except Exception as pdf_e:
                    print(f"❌ PDF simplifié corrompu: {pdf_e}")
            else:
                print(f"❌ PDF simplifié trop petit: {len(simple_pdf)} bytes")
                
        except Exception as e:
            print(f"❌ Erreur lors de la génération PDF simplifié: {e}")
            traceback.print_exc()
        
        # Étape 8: Test de la méthode complète (avec gestion d'erreur)
        print("\n🔍 Étape 8: Test de la conversion complète avec gestion d'erreur...")
        try:
            main_pdf = converter._create_main_pdf(msg, "debug-cv")
            
            if len(main_pdf) > 100:
                print(f"✅ PDF complet créé: {len(main_pdf)} bytes")
                
                with open("debug_complete_cv.pdf", "wb") as f:
                    f.write(main_pdf)
                print("✅ PDF complet sauvegardé: debug_complete_cv.pdf")
                
                # Test de validité
                from PyPDF2 import PdfReader
                try:
                    reader = PdfReader(BytesIO(main_pdf))
                    print(f"✅ PDF complet valide avec {len(reader.pages)} page(s)")
                    return True
                except Exception as pdf_e:
                    print(f"❌ PDF complet corrompu: {pdf_e}")
                    return False
            else:
                print(f"❌ PDF complet trop petit: {len(main_pdf)} bytes")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la conversion complète: {e}")
            traceback.print_exc()
            return False
        
        finally:
            try:
                msg.close()
            except:
                pass
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Debug détaillé du fichier CV.msg...")
    print("=" * 60)
    
    success = debug_cv_msg()
    
    print("=" * 60)
    if success:
        print("✅ Debug terminé avec succès!")
        print("💡 Vérifiez les fichiers PDF générés pour comparaison")
    else:
        print("❌ Problème détecté lors du debug!")
        print("💡 Consultez les messages d'erreur ci-dessus pour diagnostic")