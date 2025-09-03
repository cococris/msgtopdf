#!/usr/bin/env python3
"""
Script de debug pour la fusion des pièces jointes
"""
import sys
import os
from io import BytesIO
import traceback

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def debug_attachment_fusion():
    """Debug spécifique de la fusion des pièces jointes"""
    print("🔗 Debug de la fusion des pièces jointes...")
    print("=" * 60)
    
    try:
        from app.services.msg_converter import MSGConverter
        import extract_msg
        from PyPDF2 import PdfReader
        
        # Ouvrir le fichier CV.msg
        cv_path = "CV.msg"
        msg = extract_msg.Message(cv_path)
        converter = MSGConverter()
        
        print(f"📁 Fichier: {cv_path}")
        print(f"📎 Pièces jointes: {len(msg.attachments)}")
        
        # Étape 1: Créer le PDF principal
        print("\n🔍 Étape 1: Création du PDF principal...")
        main_pdf = converter._create_main_pdf(msg, "debug-fusion")
        print(f"✅ PDF principal: {len(main_pdf)} bytes")
        
        # Étape 2: Analyser les pièces jointes
        print("\n🔍 Étape 2: Analyse des pièces jointes...")
        for i, attachment in enumerate(msg.attachments):
            filename = attachment.longFilename or attachment.shortFilename or f"attachment_{i}"
            size = len(attachment.data) if attachment.data else 0
            print(f"  Pièce jointe {i+1}: {filename} ({size} bytes)")
            
            # Test si c'est un PDF valide
            if filename.lower().endswith('.pdf'):
                try:
                    pdf_reader = PdfReader(BytesIO(attachment.data))
                    print(f"    ✅ PDF valide avec {len(pdf_reader.pages)} page(s)")
                except Exception as e:
                    print(f"    ❌ PDF invalide: {e}")
            elif filename.lower().endswith('.docx'):
                print(f"    ⚠️ DOCX non supporté (sera ignoré)")
            else:
                print(f"    ❓ Type non reconnu")
        
        # Étape 3: Test du traitement des pièces jointes
        print("\n🔍 Étape 3: Traitement des pièces jointes...")
        try:
            attachment_pdfs = converter._process_attachments(msg, "debug-fusion", False)
            print(f"✅ Pièces jointes traitées: {len(attachment_pdfs)} PDFs prêts")
            
            for i, pdf_data in enumerate(attachment_pdfs):
                print(f"  PDF {i+1}: {len(pdf_data)} bytes")
                
                # Vérifier la validité de chaque PDF
                try:
                    reader = PdfReader(BytesIO(pdf_data))
                    print(f"    ✅ PDF valide avec {len(reader.pages)} page(s)")
                except Exception as e:
                    print(f"    ❌ PDF invalide: {e}")
                    
        except Exception as e:
            print(f"❌ Erreur lors du traitement des pièces jointes: {e}")
            traceback.print_exc()
            return False
        
        # Étape 4: Test de fusion sans pièces jointes (mode normal)
        print("\n🔍 Étape 4: Test de fusion (mode normal)...")
        try:
            if attachment_pdfs:
                print(f"Fusion de {len(attachment_pdfs)} PDF(s) avec le principal...")
                merged_pdf = converter.merge_pdfs(main_pdf, attachment_pdfs, "debug-fusion")
                print(f"✅ PDF fusionné: {len(merged_pdf)} bytes")
                
                # Sauvegarder le PDF fusionné
                with open("debug_merged_cv.pdf", "wb") as f:
                    f.write(merged_pdf)
                print("✅ PDF fusionné sauvegardé: debug_merged_cv.pdf")
                
                # Vérifier la validité du PDF fusionné
                try:
                    reader = PdfReader(BytesIO(merged_pdf))
                    print(f"✅ PDF fusionné valide avec {len(reader.pages)} page(s)")
                    
                    # Détailler les pages
                    for i, page in enumerate(reader.pages):
                        print(f"    Page {i+1}: Présente")
                        
                except Exception as e:
                    print(f"❌ PDF fusionné invalide: {e}")
                    return False
            else:
                print("⚠️ Aucun PDF à fusionner")
                merged_pdf = main_pdf
        
        except Exception as e:
            print(f"❌ Erreur lors de la fusion: {e}")
            traceback.print_exc()
            return False
        
        # Étape 5: Test de la conversion complète via l'API method
        print("\n🔍 Étape 5: Test de la conversion complète...")
        try:
            full_main_pdf, full_attachment_pdfs = converter.convert_msg_to_pdf(cv_path, "debug-full")
            print(f"✅ Conversion complète - Principal: {len(full_main_pdf)} bytes, Attachments: {len(full_attachment_pdfs)}")
            
            if full_attachment_pdfs:
                full_merged = converter.merge_pdfs(full_main_pdf, full_attachment_pdfs, "debug-full")
                print(f"✅ Fusion complète: {len(full_merged)} bytes")
                
                # Sauvegarder le résultat final
                with open("debug_final_cv.pdf", "wb") as f:
                    f.write(full_merged)
                print("✅ PDF final sauvegardé: debug_final_cv.pdf")
                
                # Vérifier la validité finale
                try:
                    reader = PdfReader(BytesIO(full_merged))
                    print(f"✅ PDF final valide avec {len(reader.pages)} page(s)")
                    
                    if len(full_merged) > 50000:  # PDF devrait être volumineux avec le CV
                        print("✅ Taille du PDF finale cohérente")
                        return True
                    else:
                        print(f"⚠️ PDF final plus petit qu'attendu: {len(full_merged)} bytes")
                        return False
                        
                except Exception as e:
                    print(f"❌ PDF final invalide: {e}")
                    return False
            else:
                print("⚠️ Pas de pièces jointes PDF à fusionner")
                return True
                
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
    print("🔗 Debug spécifique de la fusion des pièces jointes...")
    print("=" * 60)
    
    success = debug_attachment_fusion()
    
    print("=" * 60)
    if success:
        print("✅ Debug de fusion terminé avec succès!")
        print("💡 Vérifiez les fichiers PDF générés:")
        print("   - debug_merged_cv.pdf")
        print("   - debug_final_cv.pdf")
    else:
        print("❌ Problème détecté lors de la fusion!")
        print("💡 Le problème semble être dans le processus de fusion des PDFs")