#!/usr/bin/env python3
"""
Script de test pour le mode strict de validation des pièces jointes
"""
import sys
import os
import tempfile
from io import BytesIO
from PIL import Image

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def create_mock_attachment(filename: str, data: bytes = b"mock data"):
    """Crée un mock d'attachment avec les attributs nécessaires"""
    class MockAttachment:
        def __init__(self, filename, data):
            self.longFilename = filename
            self.shortFilename = filename
            self.data = data
    
    return MockAttachment(filename, data)

def create_mock_message(attachments_list):
    """Crée un mock de message avec les attachments"""
    class MockMessage:
        def __init__(self, attachments):
            self.attachments = attachments
            self.sender = "test@example.com"
            self.to = "recipient@example.com" 
            self.cc = ""
            self.subject = "Test message"
            self.date = "2024-01-01"
            self.body = "Test message body"
        
        def close(self):
            pass
    
    return MockMessage(attachments_list)

def test_strict_mode_validation():
    """Test complet du mode strict"""
    print("🧪 Test du mode strict de validation des pièces jointes...")
    print("=" * 60)
    
    try:
        from app.services.msg_converter import MSGConverter, UnauthorizedAttachmentError
        
        # Créer une instance du convertisseur
        converter = MSGConverter()
        print("✅ MSGConverter initialisé avec succès")
        
        # Test 1: Message sans pièces jointes (devrait réussir)
        print("\n📋 Test 1: Message sans pièces jointes")
        msg_empty = create_mock_message([])
        try:
            converter._validate_attachments_strict(msg_empty, "test-1")
            print("✅ Validation réussie pour message vide")
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return False
        
        # Test 2: Message avec seulement des PDFs (devrait réussir)
        print("\n📋 Test 2: Message avec seulement des PDFs")
        attachments_pdf_only = [
            create_mock_attachment("document.pdf", b"fake pdf data"),
            create_mock_attachment("rapport.PDF", b"fake pdf data 2")
        ]
        msg_pdf_only = create_mock_message(attachments_pdf_only)
        try:
            converter._validate_attachments_strict(msg_pdf_only, "test-2")
            print("✅ Validation réussie pour PDFs uniquement")
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return False
        
        # Test 3: Message avec seulement des images (devrait réussir)
        print("\n📋 Test 3: Message avec seulement des images")
        attachments_img_only = [
            create_mock_attachment("photo.jpg", b"fake jpg data"),
            create_mock_attachment("image.PNG", b"fake png data"),
            create_mock_attachment("graphic.gif", b"fake gif data")
        ]
        msg_img_only = create_mock_message(attachments_img_only)
        try:
            converter._validate_attachments_strict(msg_img_only, "test-3")
            print("✅ Validation réussie pour images uniquement")
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return False
        
        # Test 4: Message avec PDFs et images (devrait réussir)
        print("\n📋 Test 4: Message avec PDFs et images mélangés")
        attachments_mixed_valid = [
            create_mock_attachment("document.pdf", b"fake pdf data"),
            create_mock_attachment("photo.jpg", b"fake jpg data"),
            create_mock_attachment("image.webp", b"fake webp data")
        ]
        msg_mixed_valid = create_mock_message(attachments_mixed_valid)
        try:
            converter._validate_attachments_strict(msg_mixed_valid, "test-4")
            print("✅ Validation réussie pour mélange autorisé")
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return False
        
        # Test 5: Message avec fichier non autorisé (devrait échouer)
        print("\n📋 Test 5: Message avec fichier non autorisé")
        attachments_with_unauthorized = [
            create_mock_attachment("document.pdf", b"fake pdf data"),
            create_mock_attachment("virus.exe", b"fake exe data"),
            create_mock_attachment("photo.jpg", b"fake jpg data")
        ]
        msg_with_unauthorized = create_mock_message(attachments_with_unauthorized)
        try:
            converter._validate_attachments_strict(msg_with_unauthorized, "test-5")
            print("❌ ÉCHEC: La validation aurait dû échouer!")
            return False
        except UnauthorizedAttachmentError as e:
            print(f"✅ Validation échouée comme attendu: {e}")
            if "virus.exe" in str(e):
                print("✅ Le fichier non autorisé est correctement identifié")
            else:
                print("❌ Le message d'erreur ne contient pas le nom du fichier problématique")
        except Exception as e:
            print(f"❌ Erreur inattendue (attendait UnauthorizedAttachmentError): {e}")
            return False
        
        # Test 6: Message avec plusieurs fichiers non autorisés (devrait échouer)
        print("\n📋 Test 6: Message avec plusieurs fichiers non autorisés")
        attachments_multiple_unauthorized = [
            create_mock_attachment("script.bat", b"fake bat data"),
            create_mock_attachment("document.docx", b"fake docx data"),
            create_mock_attachment("photo.jpg", b"fake jpg data")
        ]
        msg_multiple_unauthorized = create_mock_message(attachments_multiple_unauthorized)
        try:
            converter._validate_attachments_strict(msg_multiple_unauthorized, "test-6")
            print("❌ ÉCHEC: La validation aurait dû échouer!")
            return False
        except UnauthorizedAttachmentError as e:
            print(f"✅ Validation échouée comme attendu: {e}")
            if "script.bat" in str(e) and "document.docx" in str(e):
                print("✅ Tous les fichiers non autorisés sont correctement identifiés")
            else:
                print("⚠️ Certains fichiers non autorisés pourraient manquer dans le message d'erreur")
        except Exception as e:
            print(f"❌ Erreur inattendue (attendait UnauthorizedAttachmentError): {e}")
            return False
        
        # Test 7: Vérification des méthodes de validation
        print("\n📋 Test 7: Vérification des méthodes de validation")
        
        # Test des extensions supportées
        test_cases = [
            ("document.pdf", True),
            ("photo.jpg", True),
            ("image.JPEG", True),
            ("graphic.png", True),
            ("animation.gif", True),
            ("bitmap.bmp", True),
            ("scan.tiff", True),
            ("modern.webp", True),
            ("archive.zip", False),
            ("script.js", False),
            ("executable.exe", False),
            ("document.docx", False),
            ("spreadsheet.xlsx", False),
            ("", False)
        ]
        
        all_validation_tests_passed = True
        for filename, expected in test_cases:
            result = converter._is_supported_attachment(filename)
            if result != expected:
                print(f"❌ Erreur validation {filename}: attendu {expected}, obtenu {result}")
                all_validation_tests_passed = False
        
        if all_validation_tests_passed:
            print("✅ Toutes les validations d'extensions sont correctes")
        else:
            return False
        
        print("\n🎉 Tous les tests de mode strict sont passés avec succès!")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Test de la fonctionnalité de mode strict...")
    print("=" * 60)
    
    success = test_strict_mode_validation()
    
    if success:
        print("=" * 60)
        print("✅ Tests de mode strict terminés avec succès!")
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Tests de mode strict échoués!")
        sys.exit(1)