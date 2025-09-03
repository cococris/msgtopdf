#!/usr/bin/env python3
"""
Script de test pour la conversion d'images en PDF
"""
import sys
import os
from io import BytesIO
from PIL import Image

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_image_conversion():
    """Test de base pour la conversion d'images"""
    try:
        from app.services.msg_converter import MSGConverter
        
        # Créer une instance du convertisseur
        converter = MSGConverter()
        print("✅ MSGConverter initialisé avec succès")
        
        # Créer une image de test simple
        test_image = Image.new('RGB', (100, 100), color='red')
        img_buffer = BytesIO()
        test_image.save(img_buffer, format='JPEG')
        img_data = img_buffer.getvalue()
        
        print(f"✅ Image de test créée ({len(img_data)} bytes)")
        
        # Tester la méthode de vérification des images supportées
        assert converter._is_supported_image("test.jpg") == True
        assert converter._is_supported_image("test.png") == True  
        assert converter._is_supported_image("test.gif") == True
        assert converter._is_supported_image("test.txt") == False
        assert converter._is_supported_image("test.pdf") == False
        print("✅ Vérification des extensions d'images supportées OK")
        
        # Tester la conversion d'image en PDF
        pdf_data = converter._convert_image_to_pdf(img_data, "test.jpg", "test-request")
        assert len(pdf_data) > 0
        print(f"✅ Conversion image vers PDF réussie ({len(pdf_data)} bytes)")
        
        # Vérifier que le PDF généré est valide
        from PyPDF2 import PdfReader
        pdf_reader = PdfReader(BytesIO(pdf_data))
        assert len(pdf_reader.pages) == 1
        print("✅ PDF généré est valide et contient 1 page")
        
        print("\n🎉 Tous les tests sont passés avec succès!")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Assurez-vous que Pillow est installé: pip install Pillow==10.1.0")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Test de la fonctionnalité de conversion d'images en PDF...")
    print("=" * 60)
    
    success = test_image_conversion()
    
    if success:
        print("=" * 60)
        print("✅ Test terminé avec succès!")
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Test échoué!")
        sys.exit(1)