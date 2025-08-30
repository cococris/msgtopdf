"""
Service de conversion des fichiers .msg en PDF
"""
import os
import tempfile
import uuid
from typing import List, Tuple, Optional
from pathlib import Path
import extract_msg
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter
import io
from datetime import datetime

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class MSGConversionError(Exception):
    """Exception pour les erreurs de conversion MSG"""
    pass


class MSGConverter:
    """Service de conversion des fichiers .msg en PDF"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés pour le PDF"""
        # Style pour les en-têtes
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Style pour les métadonnées
        self.meta_style = ParagraphStyle(
            'MetaData',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.darkgrey
        )
        
        # Style pour le contenu
        self.content_style = ParagraphStyle(
            'Content',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leftIndent=0.2*inch
        )
    
    def convert_msg_to_pdf(self, msg_file_path: str, request_id: str) -> Tuple[bytes, List[bytes]]:
        """
        Convertit un fichier .msg en PDF et retourne les PDFs des pièces jointes
        
        Args:
            msg_file_path: Chemin vers le fichier .msg
            request_id: ID de la requête pour le logging
            
        Returns:
            Tuple contenant (PDF du mail, Liste des PDFs des pièces jointes)
        """
        logger.info(f"[{request_id}] Début de conversion du fichier: {msg_file_path}")
        
        try:
            # Extraction du message
            msg = extract_msg.Message(msg_file_path)
            
            # Création du PDF principal
            main_pdf = self._create_main_pdf(msg, request_id)
            
            # Traitement des pièces jointes
            attachment_pdfs = self._process_attachments(msg, request_id)
            
            logger.info(f"[{request_id}] Conversion terminée avec succès")
            return main_pdf, attachment_pdfs
            
        except Exception as e:
            logger.error(f"[{request_id}] Erreur lors de la conversion: {e}")
            raise MSGConversionError(f"Erreur de conversion: {e}")
        finally:
            try:
                msg.close()
            except:
                pass
    
    def _create_main_pdf(self, msg: extract_msg.Message, request_id: str) -> bytes:
        """Crée le PDF principal à partir du message"""
        logger.debug(f"[{request_id}] Création du PDF principal")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # En-tête du document
        story.append(Paragraph("Email Outlook", self.header_style))
        story.append(Spacer(1, 12))
        
        # Métadonnées du message
        metadata_table = self._create_metadata_table(msg)
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        # Contenu du message
        if msg.body:
            story.append(Paragraph("Contenu:", self.header_style))
            story.append(Spacer(1, 6))
            
            # Nettoyage et formatage du contenu
            content = self._clean_content(msg.body)
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    story.append(Paragraph(paragraph.strip(), self.content_style))
                    story.append(Spacer(1, 6))
        
        # Informations sur les pièces jointes
        if msg.attachments:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Pièces jointes:", self.header_style))
            story.append(Spacer(1, 6))
            
            attachment_data = []
            for i, attachment in enumerate(msg.attachments):
                attachment_data.append([
                    str(i + 1),
                    attachment.longFilename or attachment.shortFilename or "Sans nom",
                    f"{len(attachment.data) if attachment.data else 0} bytes"
                ])
            
            attachment_table = Table(
                [["#", "Nom du fichier", "Taille"]] + attachment_data,
                colWidths=[0.5*inch, 4*inch, 1.5*inch]
            )
            attachment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(attachment_table)
        
        # Construction du PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_metadata_table(self, msg: extract_msg.Message) -> Table:
        """Crée un tableau avec les métadonnées du message"""
        metadata = [
            ["De:", msg.sender or "Non spécifié"],
            ["À:", msg.to or "Non spécifié"],
            ["CC:", msg.cc or ""],
            ["Objet:", msg.subject or "Sans objet"],
            ["Date:", self._format_date(msg.date)],
        ]
        
        table = Table(metadata, colWidths=[1*inch, 5*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        return table
    
    def _clean_content(self, content: str) -> str:
        """Nettoie le contenu du message pour l'affichage PDF"""
        if not content:
            return ""
        
        # Suppression des caractères de contrôle
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
        
        # Limitation de la longueur des lignes
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if len(line) > 100:
                # Découpage des lignes trop longues
                words = line.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line + word) > 100:
                        if current_line:
                            cleaned_lines.append(current_line.strip())
                            current_line = word + " "
                        else:
                            cleaned_lines.append(word)
                            current_line = ""
                    else:
                        current_line += word + " "
                if current_line:
                    cleaned_lines.append(current_line.strip())
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _format_date(self, date) -> str:
        """Formate la date pour l'affichage"""
        if not date:
            return "Non spécifiée"
        
        try:
            if isinstance(date, str):
                return date
            return date.strftime("%d/%m/%Y %H:%M:%S")
        except:
            return str(date)
    
    def _process_attachments(self, msg: extract_msg.Message, request_id: str) -> List[bytes]:
        """Traite les pièces jointes et retourne les PDFs"""
        pdf_attachments = []
        
        if not msg.attachments:
            logger.info(f"[{request_id}] ❌ Aucune pièce jointe trouvée dans le message")
            return pdf_attachments
        
        logger.info(f"[{request_id}] 📎 Traitement de {len(msg.attachments)} pièce(s) jointe(s)")
        
        for i, attachment in enumerate(msg.attachments):
            try:
                # Nettoyage du nom de fichier (suppression des caractères null)
                raw_filename = attachment.longFilename or attachment.shortFilename or f"attachment_{i}"
                filename = raw_filename.rstrip('\x00').strip()  # Supprime les caractères null et espaces
                file_size = len(attachment.data) if attachment.data else 0
                logger.info(f"[{request_id}] 📄 Pièce jointe {i+1}: '{filename}' ({file_size} bytes)")
                
                # Vérification du type de fichier
                if filename.lower().endswith('.pdf'):
                    if attachment.data and len(attachment.data) > 0:
                        pdf_attachments.append(attachment.data)
                        logger.info(f"[{request_id}] ✅ PDF ajouté pour fusion: {filename} ({len(attachment.data)} bytes)")
                    else:
                        logger.warning(f"[{request_id}] ⚠️ Pièce jointe PDF vide ignorée: {filename}")
                else:
                    logger.info(f"[{request_id}] ❌ Type de fichier non-PDF ignoré: {filename}")
                    
            except Exception as e:
                logger.error(f"[{request_id}] ❌ Erreur lors du traitement de la pièce jointe {i}: {e}")
                continue
        
        if pdf_attachments:
            logger.info(f"[{request_id}] 🎯 {len(pdf_attachments)} PDF(s) prêts pour la fusion")
        else:
            logger.info(f"[{request_id}] ❌ Aucun PDF trouvé dans les pièces jointes")
        
        return pdf_attachments
    
    def merge_pdfs(self, main_pdf: bytes, attachment_pdfs: List[bytes], request_id: str) -> bytes:
        """Fusionne le PDF principal avec les PDFs des pièces jointes"""
        if not attachment_pdfs:
            logger.debug(f"[{request_id}] Aucun PDF à fusionner, retour du PDF principal")
            return main_pdf
        
        logger.info(f"[{request_id}] Fusion de {len(attachment_pdfs)} PDF(s) de pièces jointes")
        
        try:
            writer = PdfWriter()
            
            # Ajout du PDF principal
            main_reader = PdfReader(io.BytesIO(main_pdf))
            for page in main_reader.pages:
                writer.add_page(page)
            
            # Ajout des PDFs des pièces jointes
            for i, pdf_data in enumerate(attachment_pdfs):
                try:
                    reader = PdfReader(io.BytesIO(pdf_data))
                    for page in reader.pages:
                        writer.add_page(page)
                    logger.debug(f"[{request_id}] PDF de pièce jointe {i+1} fusionné")
                except Exception as e:
                    logger.error(f"[{request_id}] Erreur lors de la fusion du PDF {i+1}: {e}")
                    continue
            
            # Génération du PDF final
            output_buffer = io.BytesIO()
            writer.write(output_buffer)
            output_buffer.seek(0)
            
            result = output_buffer.getvalue()
            logger.info(f"[{request_id}] Fusion terminée, taille finale: {len(result)} bytes")
            return result
            
        except Exception as e:
            logger.error(f"[{request_id}] Erreur lors de la fusion des PDFs: {e}")
            raise MSGConversionError(f"Erreur de fusion: {e}")