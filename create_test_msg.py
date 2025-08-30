"""
Créateur de fichier MSG de test avec pièce jointe PDF simulée
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def create_test_pdf():
    """Crée un PDF de test simple"""
    pdf_path = "test_attachment.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    
    story = []
    story.append(Paragraph("Ceci est un PDF de test en pièce jointe", styles['Title']))
    story.append(Paragraph("Ce PDF devrait être fusionné avec l'email converti.", styles['Normal']))
    
    doc.build(story)
    return pdf_path

def create_mock_msg_with_pdf():
    """Crée un fichier MSG simulé avec métadonnées"""
    # Créer le PDF de test
    pdf_path = create_test_pdf()
    
    # Lire le contenu du PDF
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    print(f"✅ PDF de test créé: {pdf_path} ({len(pdf_content)} bytes)")
    
    # Instructions pour tester
    print("\n📋 Instructions de test:")
    print("1. Utilisez un vrai fichier .msg d'Outlook avec une pièce jointe PDF")
    print("2. Ou testez avec le fichier simple pour voir les logs")
    print("3. Vérifiez les logs de l'API pour voir le traitement des pièces jointes")
    
    return pdf_path

if __name__ == "__main__":
    create_mock_msg_with_pdf()