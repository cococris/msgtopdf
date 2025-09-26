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
from PIL import Image

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class MSGConversionError(Exception):
    """Exception pour les erreurs de conversion MSG"""
    pass


class UnauthorizedAttachmentError(MSGConversionError):
    """Exception pour les pièces jointes non autorisées"""
    pass


class MSGConverter:
    """Service de conversion des fichiers .msg en PDF"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés pour le PDF"""
        # Style pour le titre principal - simplifié
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=15,
            spaceBefore=10,
            textColor=colors.black,
            alignment=0,  # Aligné à gauche
            fontName='Helvetica-Bold'
        )
        
        # Style pour les en-têtes de sections - simplifié
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=15,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Style uniforme pour les métadonnées (label + valeur sur la même ligne)
        self.meta_style = ParagraphStyle(
            'MetaData',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.black,
            fontName='Helvetica'
        )
        
        # Style pour le corps de l'email
        self.body_style = ParagraphStyle(
            'EmailBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            spaceBefore=3,
            leftIndent=0.1*inch,
            rightIndent=0.1*inch,
            textColor=colors.black,
            leading=14
        )
        
        # Style pour les paragraphes du corps
        self.paragraph_style = ParagraphStyle(
            'Paragraph',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            spaceBefore=4,
            leftIndent=0.1*inch,
            rightIndent=0.1*inch,
            textColor=colors.black,
            leading=14
        )
        
        # Style pour les séparateurs
        self.separator_style = ParagraphStyle(
            'Separator',
            parent=self.styles['Normal'],
            fontSize=1,
            spaceAfter=10,
            spaceBefore=10,
            alignment=1
        )
    
    def convert_msg_to_pdf(self, msg_file_path: str, request_id: str, strict_mode: bool = False) -> Tuple[bytes, List[bytes]]:
        """
        Convertit un fichier .msg en PDF et retourne les PDFs des pièces jointes
        
        Args:
            msg_file_path: Chemin vers le fichier .msg
            request_id: ID de la requête pour le logging
            strict_mode: Si True, refuse la conversion si des pièces jointes non autorisées sont présentes
            
        Returns:
            Tuple contenant (PDF du mail, Liste des PDFs des pièces jointes)
        """
        logger.info(f"[{request_id}] Début de conversion du fichier: {msg_file_path}")
        
        try:
            # Extraction du message
            msg = extract_msg.Message(msg_file_path)
            
            # Validation stricte des pièces jointes si activée
            if strict_mode:
                self._validate_attachments_strict(msg, request_id)
            
            # Création du PDF principal
            main_pdf = self._create_main_pdf(msg, request_id)
            
            # Traitement des pièces jointes
            attachment_pdfs = self._process_attachments(msg, request_id, strict_mode)
            
            logger.info(f"[{request_id}] Conversion terminée avec succès")
            return main_pdf, attachment_pdfs
            
        except UnauthorizedAttachmentError:
            # Re-lancer l'UnauthorizedAttachmentError directement (ne pas l'encapsuler)
            raise
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
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.8*inch,
            bottomMargin=0.8*inch,
            leftMargin=0.7*inch,
            rightMargin=0.7*inch
        )
        story = []
        
        # Titre principal du document
        story.append(Paragraph("Email Outlook", self.title_style))
        story.append(Spacer(1, 10))
        
        # Métadonnées formatées de manière simple
        self._add_metadata_section(story, msg)
        story.append(Spacer(1, 15))
        
        # Créer une liste des pièces jointes images pour les placeholders
        image_attachments = []
        if msg.attachments:
            for i, attachment in enumerate(msg.attachments):
                filename = attachment.longFilename or attachment.shortFilename or f"attachment_{i}"
                filename = filename.rstrip('\x00').strip()
                if self._is_supported_image(filename):
                    image_attachments.append(filename)
        
        # Section du contenu du message
        if msg.body:
            story.append(Paragraph("Contenu du message", self.header_style))
            story.append(Spacer(1, 10))
            
            # Formatage amélioré du contenu avec placeholders d'images
            self._add_email_body_section(story, msg.body, image_attachments)
        else:
            story.append(Paragraph("Contenu du message", self.header_style))
            story.append(Spacer(1, 8))
            story.append(Paragraph("<i>Aucun contenu textuel disponible</i>", self.body_style))
        
        # Ajouter les placeholders d'images si pas de body ou si images pas référencées
        if image_attachments:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Images jointes à cet email :", self.header_style))
            story.append(Spacer(1, 5))
            for filename in image_attachments:
                story.append(Paragraph(f"• <b>[IMAGE: {filename}]</b> - Voir pages suivantes", self.meta_style))
        
        story.append(Spacer(1, 15))
        
        # Informations sur les pièces jointes
        if msg.attachments:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Pièces jointes", self.header_style))
            story.append(Spacer(1, 8))
            
            attachment_table = self._create_simple_attachment_table(msg.attachments)
            story.append(attachment_table)
        
        # Construction du PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    
    def _add_metadata_section(self, story, msg: extract_msg.Message):
        """Ajoute la section des métadonnées de manière simple et unifiée"""
        # De
        if msg.sender:
            story.append(Paragraph(f"<b>De:</b> {msg.sender}", self.meta_style))
        
        # À
        if msg.to:
            story.append(Paragraph(f"<b>À:</b> {msg.to}", self.meta_style))
        
        # CC
        if msg.cc:
            story.append(Paragraph(f"<b>CC:</b> {msg.cc}", self.meta_style))
        
        # Objet
        story.append(Paragraph(f"<b>Objet:</b> {msg.subject or 'Sans objet'}", self.meta_style))
        
        # Date
        story.append(Paragraph(f"<b>Date:</b> {self._format_date(msg.date)}", self.meta_style))
    
    def _add_email_body_section(self, story, body_text: str, image_attachments: list = None):
        """Ajoute le contenu de l'email avec un formatage amélioré et des placeholders d'images"""
        if not body_text:
            return
        
        # Nettoyage et formatage du contenu
        content = self._clean_content(body_text)
        
        # Rechercher et remplacer les références d'images communes dans le contenu
        if image_attachments:
            import re
            for filename in image_attachments:
                # Rechercher des références possibles à l'image dans le texte
                pattern = re.compile(re.escape(filename), re.IGNORECASE)
                placeholder = f"[IMAGE: {filename} - Voir pages suivantes]"
                content = pattern.sub(placeholder, content)
            
            # Rechercher d'autres patterns d'images courantes
            # Pattern pour les références d'images génériques
            img_patterns = [
                r'<img[^>]*>',  # Balises img HTML
                r'\[image:[^\]]*\]',  # Format [image:...]
                r'\[cid:[^\]]*\]'  # Content-ID references
            ]
            
            for pattern in img_patterns:
                content = re.sub(pattern, '[IMAGE - Voir pièces jointes]', content, flags=re.IGNORECASE)
        
        # Diviser le contenu en paragraphes plus intelligemment
        paragraphs = []
        current_paragraph = ""
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:  # Ligne vide
                if current_paragraph:
                    paragraphs.append(current_paragraph.strip())
                    current_paragraph = ""
            else:
                if current_paragraph:
                    current_paragraph += " " + line
                else:
                    current_paragraph = line
        
        # Ajouter le dernier paragraphe s'il existe
        if current_paragraph:
            paragraphs.append(current_paragraph.strip())
        
        # Ajouter chaque paragraphe au PDF
        for i, paragraph in enumerate(paragraphs):
            if paragraph:
                # Échapper les caractères HTML pour éviter les erreurs (sauf nos placeholders)
                safe_paragraph = paragraph.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                # Remettre en gras nos placeholders d'images
                safe_paragraph = safe_paragraph.replace('[IMAGE:', '<b>[IMAGE:').replace(']', ']</b>')
                
                story.append(Paragraph(safe_paragraph, self.paragraph_style))
                
                # Ajouter un espacement entre les paragraphes (pas après le dernier)
                if i < len(paragraphs) - 1:
                    story.append(Spacer(1, 4))
    
    def _create_simple_attachment_table(self, attachments) -> Table:
        """Crée un tableau simple pour les pièces jointes"""
        attachment_data = []
        for i, attachment in enumerate(attachments):
            filename = attachment.longFilename or attachment.shortFilename or "Sans nom"
            file_size = len(attachment.data) if attachment.data else 0
            
            # Formatage de la taille
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            # Déterminer le type de fichier
            file_ext = filename.split('.')[-1].lower() if '.' in filename else "?"
            if file_ext == 'pdf':
                file_type = "PDF"
            elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp']:
                file_type = "Image"
            else:
                file_type = f"{file_ext.upper()}"
            
            attachment_data.append([
                str(i + 1),
                file_type,
                filename,
                size_str
            ])
        
        table = Table(
            [["#", "Type", "Nom du fichier", "Taille"]] + attachment_data,
            colWidths=[0.4*inch, 0.8*inch, 3.5*inch, 1*inch]
        )
        table.setStyle(TableStyle([
            # En-tête simple
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            
            # Corps du tableau
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            
            # Bordures simples
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _clean_content(self, content: str) -> str:
        """Nettoie le contenu du message pour l'affichage PDF"""
        if not content:
            return ""
        
        # Suppression des caractères de contrôle (sauf retours à la ligne)
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
        
        # Nettoyage des espaces multiples et caractères indésirables
        import re
        content = re.sub(r' +', ' ', content)  # Remplace les espaces multiples par un seul
        content = re.sub(r'\t+', ' ', content)  # Remplace les tabulations par des espaces
        
        # Suppression des lignes vides multiples consecutives
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Suppression des espaces en début et fin de lignes
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Gestion intelligente des longues lignes (découpage aux mots)
            if len(line) > 80:  # Limite plus raisonnable pour la lisibilité
                words = line.split(' ')
                current_line = ""
                
                for word in words:
                    # Si ajouter ce mot dépasse la limite
                    if len(current_line + ' ' + word) > 80:
                        if current_line:  # Si la ligne courante n'est pas vide
                            cleaned_lines.append(current_line.strip())
                            current_line = word
                        else:  # Le mot seul est trop long
                            cleaned_lines.append(word)
                            current_line = ""
                    else:
                        if current_line:
                            current_line += ' ' + word
                        else:
                            current_line = word
                
                # Ajouter la dernière ligne si elle n'est pas vide
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
    
    def _convert_image_to_pdf(self, image_data: bytes, filename: str, request_id: str) -> bytes:
        """Convertit une image en PDF avec orientation adaptée au format"""
        logger.debug(f"[{request_id}] Conversion de l'image {filename} en PDF")
        
        try:
            # Ouvrir l'image avec Pillow
            image = Image.open(io.BytesIO(image_data))
            
            # Convertir en RGB si nécessaire (pour gérer les images PNG avec transparence, etc.)
            if image.mode != 'RGB':
                # Créer un fond blanc pour les images avec transparence
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'RGBA':
                        background.paste(image, mask=image.split()[-1])  # Utilise le canal alpha comme masque
                    else:
                        background.paste(image, mask=image.split()[-1])
                    image = background
                else:
                    image = image.convert('RGB')
            
            # Créer un PDF avec l'image
            buffer = io.BytesIO()
            
            # Déterminer l'orientation optimale selon le format de l'image
            img_width, img_height = image.size
            is_landscape = img_width > img_height
            
            # Choisir l'orientation de la page selon le format de l'image
            if is_landscape:
                from reportlab.lib.pagesizes import landscape
                page_size = landscape(A4)
                orientation = "paysage"
            else:
                page_size = A4
                orientation = "portrait"
            
            logger.debug(f"[{request_id}] Image {filename} ({img_width}x{img_height}) -> Orientation {orientation}")
            
            # Calculer les dimensions pour adapter l'image à la page
            page_width, page_height = page_size
            
            # Calculer le ratio pour adapter l'image sans déformation
            ratio = min(page_width / img_width, page_height / img_height)
            new_width = img_width * ratio
            new_height = img_height * ratio
            
            # Créer le document PDF avec l'orientation adaptée
            doc = SimpleDocTemplate(buffer, pagesize=page_size)
            story = []
            
            # Ajouter un titre avec le nom du fichier
            story.append(Paragraph(f"Image: {filename}", self.header_style))
            story.append(Spacer(1, 12))
            
            # Sauvegarder temporairement l'image redimensionnée
            temp_img_buffer = io.BytesIO()
            resized_image = image.resize((int(new_width), int(new_height)), Image.Resampling.LANCZOS)
            resized_image.save(temp_img_buffer, format='JPEG', quality=85)
            temp_img_buffer.seek(0)
            
            # Ajouter l'image au PDF en utilisant reportlab
            from reportlab.platypus import Image as RLImage
            rl_image = RLImage(temp_img_buffer, width=new_width, height=new_height)
            story.append(rl_image)
            
            # Construire le PDF
            doc.build(story)
            buffer.seek(0)
            
            result = buffer.getvalue()
            logger.info(f"[{request_id}] Image {filename} convertie en PDF {orientation} ({len(result)} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"[{request_id}] Erreur lors de la conversion de l'image {filename}: {e}")
            raise MSGConversionError(f"Erreur de conversion d'image {filename}: {e}")
    
    def _is_supported_image(self, filename: str) -> bool:
        """Vérifie si le fichier est une image supportée"""
        supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        return Path(filename.lower()).suffix in supported_extensions
    
    def _is_supported_attachment(self, filename: str) -> bool:
        """Vérifie si le fichier est une pièce jointe supportée (PDF ou image)"""
        return filename.lower().endswith('.pdf') or self._is_supported_image(filename)
    
    def _validate_attachments_strict(self, msg: extract_msg.Message, request_id: str):
        """Valide que toutes les pièces jointes sont autorisées en mode strict"""
        if not msg.attachments:
            return
        
        unauthorized_files = []
        
        for i, attachment in enumerate(msg.attachments):
            try:
                raw_filename = attachment.longFilename or attachment.shortFilename or f"attachment_{i}"
                filename = raw_filename.rstrip('\x00').strip()
                
                if not self._is_supported_attachment(filename):
                    unauthorized_files.append(filename)
                    logger.warning(f"[{request_id}] Pièce jointe non autorisée détectée: {filename}")
                    
            except Exception as e:
                logger.error(f"[{request_id}] Erreur lors de la validation de la pièce jointe {i}: {e}")
                unauthorized_files.append(f"attachment_{i}")
        
        if unauthorized_files:
            error_msg = f"Pièces jointes non autorisées détectées: {', '.join(unauthorized_files)}. Seuls les PDFs et images (JPG, PNG, GIF, BMP, TIFF, WebP) sont acceptés."
            logger.error(f"[{request_id}] Conversion refusée en mode strict: {error_msg}")
            raise UnauthorizedAttachmentError(error_msg)
        
        logger.info(f"[{request_id}] Toutes les pièces jointes sont autorisées ({len(msg.attachments)} fichiers validés)")
    
    def _process_attachments(self, msg: extract_msg.Message, request_id: str, strict_mode: bool = False) -> List[bytes]:
        """Traite les pièces jointes et retourne les PDFs"""
        pdf_attachments = []
        
        if not msg.attachments:
            logger.info(f"[{request_id}] Aucune pièce jointe trouvée dans le message")
            return pdf_attachments
        
        logger.info(f"[{request_id}] Traitement de {len(msg.attachments)} pièce(s) jointe(s)")
        
        for i, attachment in enumerate(msg.attachments):
            try:
                # Nettoyage du nom de fichier (suppression des caractères null)
                raw_filename = attachment.longFilename or attachment.shortFilename or f"attachment_{i}"
                filename = raw_filename.rstrip('\x00').strip()  # Supprime les caractères null et espaces
                file_size = len(attachment.data) if attachment.data else 0
                logger.info(f"[{request_id}] Pièce jointe {i+1}: '{filename}' ({file_size} bytes)")
                
                # Vérification du type de fichier
                if filename.lower().endswith('.pdf'):
                    if attachment.data and len(attachment.data) > 0:
                        pdf_attachments.append(attachment.data)
                        logger.info(f"[{request_id}] PDF ajouté pour fusion: {filename} ({len(attachment.data)} bytes)")
                    else:
                        logger.warning(f"[{request_id}] Pièce jointe PDF vide ignorée: {filename}")
                elif self._is_supported_image(filename):
                    if attachment.data and len(attachment.data) > 0:
                        # Convertir l'image en PDF
                        try:
                            image_pdf = self._convert_image_to_pdf(attachment.data, filename, request_id)
                            pdf_attachments.append(image_pdf)
                            logger.info(f"[{request_id}] Image convertie et ajoutée pour fusion: {filename} ({len(image_pdf)} bytes)")
                        except Exception as e:
                            logger.error(f"[{request_id}] Erreur lors de la conversion de l'image {filename}: {e}")
                            continue
                    else:
                        logger.warning(f"[{request_id}] Pièce jointe image vide ignorée: {filename}")
                else:
                    if strict_mode:
                        # En mode strict, cela ne devrait pas arriver car on a déjà validé
                        logger.error(f"[{request_id}] ERREUR: Pièce jointe non autorisée détectée après validation: {filename}")
                    else:
                        logger.info(f"[{request_id}] Type de fichier non supporté ignoré: {filename}")
                    
            except Exception as e:
                logger.error(f"[{request_id}] Erreur lors du traitement de la pièce jointe {i}: {e}")
                continue
        
        if pdf_attachments:
            logger.info(f"[{request_id}] {len(pdf_attachments)} PDF(s) prêts pour la fusion (PDFs originaux + images converties)")
        else:
            logger.info(f"[{request_id}] Aucun PDF ni image supportée trouvé dans les pièces jointes")
        
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