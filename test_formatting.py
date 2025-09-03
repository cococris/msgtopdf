#!/usr/bin/env python3
"""
Script de test pour la nouvelle mise en forme PDF
"""
import sys
import os
from io import BytesIO

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def create_mock_message_with_content():
    """Crée un mock de message avec du contenu réaliste"""
    class MockAttachment:
        def __init__(self, filename, data, long_filename=None):
            self.longFilename = long_filename or filename
            self.shortFilename = filename
            self.data = data
    
    class MockMessage:
        def __init__(self):
            self.sender = "Jean Dupont <jean.dupont@entreprise.com>"
            self.to = "équipe-dev@entreprise.com; marie.martin@entreprise.com"
            self.cc = "manager@entreprise.com"
            self.subject = "Rapport mensuel - Projet Alpha - Analyse des performances"
            self.date = "2024-01-15 14:30:25"
            
            # Contenu réaliste d'un email
            self.body = """Bonjour l'équipe,

J'espère que vous allez bien. Voici le rapport mensuel concernant le projet Alpha que nous avons développé ensemble ce mois-ci.

## Résumé Exécutif

Le projet a bien avancé avec plusieurs réalisations importantes :
- Migration de la base de données terminée avec succès
- Optimisation des performances : amélioration de 35% du temps de réponse
- Correction de 24 bugs critiques et 67 bugs mineurs
- Implémentation de 12 nouvelles fonctionnalités demandées par les clients

## Métriques de Performance

Les tests de charge ont montré des résultats encourageants. Le système peut maintenant gérer jusqu'à 10,000 utilisateurs simultanés sans dégradation notable des performances. C'est une amélioration significative par rapport aux 7,500 utilisateurs du mois précédent.

## Défis Rencontrés

Nous avons rencontré quelques difficultés techniques :
1. Problème de compatibilité avec les anciens navigateurs (Internet Explorer)
2. Latence réseau plus élevée que prévu en Asie
3. Quelques bugs intermittents lors des pics de charge

## Prochaines Étapes

Pour le mois prochain, nous prévoyons de :
- Finaliser la phase de tests utilisateurs
- Déployer en production sur l'environnement principal
- Former les équipes support sur les nouvelles fonctionnalités
- Préparer la documentation utilisateur finale

J'ai joint quelques documents techniques en pièces jointes pour votre référence.

Merci pour votre excellent travail et n'hésitez pas si vous avez des questions.

Cordialement,
Jean Dupont
Chef de Projet Technique
Département IT - Division R&D"""

            # Pièces jointes variées
            self.attachments = [
                MockAttachment("Rapport_Performance.pdf", b"fake pdf content" * 100),
                MockAttachment("Graphiques_Stats.jpg", b"fake jpg content" * 50),
                MockAttachment("Architecture_System.png", b"fake png content" * 75),
                MockAttachment("Budget_Previsionnel.xlsx", b"fake excel content" * 30)  # Non autorisé en mode strict
            ]
        
        def close(self):
            pass
    
    return MockMessage()

def test_pdf_formatting():
    """Test de la nouvelle mise en forme PDF"""
    print("🎨 Test de la nouvelle mise en forme PDF...")
    print("=" * 60)
    
    try:
        from app.services.msg_converter import MSGConverter
        
        # Créer une instance du convertisseur
        converter = MSGConverter()
        print("✅ MSGConverter initialisé avec succès")
        
        # Créer un message de test avec contenu réaliste
        msg = create_mock_message_with_content()
        print("✅ Message de test créé avec contenu réaliste")
        
        # Test de la méthode de nettoyage du contenu
        cleaned_content = converter._clean_content(msg.body)
        print(f"✅ Contenu nettoyé: {len(cleaned_content)} caractères")
        
        # Vérifier que le contenu est bien formaté
        lines = cleaned_content.split('\n')
        long_lines = [line for line in lines if len(line) > 80]
        if long_lines:
            print(f"⚠️  {len(long_lines)} lignes encore trop longues trouvées")
            for i, line in enumerate(long_lines[:3]):  # Afficher les 3 premières
                print(f"   Ligne {i+1}: {len(line)} caractères")
        else:
            print("✅ Toutes les lignes respectent la limite de 80 caractères")
        
        # Test de création du PDF principal
        print("\n📄 Test de génération du PDF principal...")
        main_pdf = converter._create_main_pdf(msg, "test-formatting")
        print(f"✅ PDF principal généré: {len(main_pdf)} bytes")
        
        # Vérifier que le PDF est valide
        from PyPDF2 import PdfReader
        pdf_reader = PdfReader(BytesIO(main_pdf))
        num_pages = len(pdf_reader.pages)
        print(f"✅ PDF valide avec {num_pages} page(s)")
        
        # Test de création du tableau des pièces jointes
        print("\n📎 Test du tableau des pièces jointes amélioré...")
        attachment_table = converter._create_enhanced_attachment_table(msg.attachments)
        print("✅ Tableau des pièces jointes créé avec succès")
        
        # Test en mode strict (devrait échouer avec le fichier Excel)
        print("\n🔒 Test du mode strict avec pièce jointe non autorisée...")
        try:
            converter._validate_attachments_strict(msg, "test-strict-formatting")
            print("❌ ERREUR: Le mode strict aurait dû échouer!")
            return False
        except Exception as e:
            print(f"✅ Mode strict a correctement échoué: {type(e).__name__}")
        
        # Test de formatage des métadonnées
        print("\n📋 Test du formatage des métadonnées...")
        story = []
        converter._add_metadata_section(story, msg)
        print(f"✅ Section métadonnées créée avec {len(story)} éléments")
        
        # Test de formatage du corps de l'email
        print("\n📄 Test du formatage du corps de l'email...")
        story = []
        converter._add_email_body_section(story, msg.body)
        print(f"✅ Section corps de l'email créée avec {len(story)} paragraphes")
        
        # Sauvegarder un exemple de PDF pour vérification visuelle
        print("\n💾 Génération d'un PDF de test pour vérification visuelle...")
        with open("test_formatting_output.pdf", "wb") as f:
            f.write(main_pdf)
        print("✅ PDF de test sauvegardé: test_formatting_output.pdf")
        
        print("\n🎉 Tous les tests de formatage sont passés avec succès!")
        print("\n📋 Résumé des améliorations:")
        print("   • Titre principal avec emoji centré")
        print("   • Sections bien séparées avec en-têtes colorés")
        print("   • Métadonnées formatées avec icônes")
        print("   • Contenu du message en paragraphes lisibles")
        print("   • Tableau des pièces jointes amélioré avec types et icônes")
        print("   • Séparateurs visuels entre les sections")
        print("   • Mise en page professionnelle avec marges ajustées")
        
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
    print("🎨 Test de la nouvelle mise en forme PDF améliorée...")
    print("=" * 60)
    
    success = test_pdf_formatting()
    
    if success:
        print("=" * 60)
        print("✅ Tests de formatage terminés avec succès!")
        print("\n💡 Vous pouvez ouvrir 'test_formatting_output.pdf' pour voir le résultat")
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Tests de formatage échoués!")
        sys.exit(1)