#!/usr/bin/env python3
"""
Test direct du mode strict sans API
"""
import sys
import os
import traceback

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_direct_strict():
    """Test direct du mode strict"""
    print("🔍 Test direct du mode strict...")
    print("=" * 50)
    
    try:
        from app.services.msg_converter import MSGConverter, UnauthorizedAttachmentError
        
        cv_path = "CV.msg"
        converter = MSGConverter()
        
        print("✅ Imports réussis")
        print(f"📁 Fichier: {cv_path}")
        
        # Test en mode strict
        print("\n🔒 Test en mode strict...")
        try:
            main_pdf, attachment_pdfs = converter.convert_msg_to_pdf(cv_path, "test-direct-strict", strict_mode=True)
            print("❌ ERREUR: Le mode strict aurait dû échouer!")
            return False
            
        except UnauthorizedAttachmentError as e:
            print(f"✅ UnauthorizedAttachmentError capturée correctement: {e}")
            return True
            
        except Exception as e:
            print(f"❌ Exception inattendue: {type(e).__name__}: {e}")
            traceback.print_exc()
            return False
            
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_strict()
    
    if success:
        print("\n✅ Mode strict fonctionne correctement au niveau du service")
        print("💡 Le problème est probablement dans la capture d'exception de l'API")
    else:
        print("\n❌ Problème au niveau du service lui-même")