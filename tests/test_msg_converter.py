"""
Tests pour le service de conversion MSG
"""
import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from app.services.msg_converter import MSGConverter, MSGConversionError


class TestMSGConverter:
    """Tests pour le convertisseur MSG"""
    
    @pytest.fixture
    def converter(self):
        """Instance du convertisseur pour les tests"""
        return MSGConverter()
    
    def test_converter_initialization(self, converter):
        """Test d'initialisation du convertisseur"""
        assert converter is not None
        assert hasattr(converter, 'styles')
        assert hasattr(converter, 'header_style')
        assert hasattr(converter, 'meta_style')
        assert hasattr(converter, 'content_style')
    
    def test_convert_msg_to_pdf_success(self, converter, mock_extract_msg):
        """Test de conversion réussie d'un fichier MSG"""
        request_id = "test-request-123"
        msg_file_path = "/tmp/test.msg"
        
        with patch('app.services.msg_converter.extract_msg.Message') as mock_msg_class:
            mock_msg_class.return_value = mock_extract_msg
            
            with patch.object(converter, '_create_main_pdf') as mock_create_pdf, \
                 patch.object(converter, '_process_attachments') as mock_process_att:
                
                mock_create_pdf.return_value = b"PDF content"
                mock_process_att.return_value = [b"Attachment PDF"]
                
                main_pdf, attachment_pdfs = converter.convert_msg_to_pdf(msg_file_path, request_id)
                
                assert main_pdf == b"PDF content"
                assert attachment_pdfs == [b"Attachment PDF"]
                mock_extract_msg.close.assert_called_once()
    
    def test_convert_msg_to_pdf_error(self, converter):
        """Test d'erreur lors de la conversion"""
        request_id = "test-request-123"
        msg_file_path = "/tmp/test.msg"
        
        with patch('app.services.msg_converter.extract_msg.Message') as mock_msg_class:
            mock_msg_class.side_effect = Exception("File not found")
            
            with pytest.raises(MSGConversionError, match="Erreur de conversion"):
                converter.convert_msg_to_pdf(msg_file_path, request_id)
    
    def test_create_main_pdf(self, converter, mock_extract_msg):
        """Test de création du PDF principal"""
        request_id = "test-request-123"
        
        # Configuration du message mocké avec plus de détails
        mock_extract_msg.sender = "sender@example.com"
        mock_extract_msg.to = "recipient@example.com"
        mock_extract_msg.cc = "cc@example.com"
        mock_extract_msg.subject = "Test Subject"
        mock_extract_msg.date = "2023-01-01 12:00:00"
        mock_extract_msg.body = "Test email body content\n\nSecond paragraph"
        mock_extract_msg.attachments = []
        
        pdf_content = converter._create_main_pdf(mock_extract_msg, request_id)
        
        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
        # Vérification que c'est un PDF valide
        assert pdf_content.startswith(b'%PDF')
    
    def test_create_main_pdf_with_attachments(self, converter, mock_extract_msg):
        """Test de création du PDF avec pièces jointes"""
        request_id = "test-request-123"
        
        # Mock des pièces jointes
        mock_attachment = Mock()
        mock_attachment.longFilename = "document.pdf"
        mock_attachment.shortFilename = "doc.pdf"
        mock_attachment.data = b"PDF attachment data"
        
        mock_extract_msg.attachments = [mock_attachment]
        
        pdf_content = converter._create_main_pdf(mock_extract_msg, request_id)
        
        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
    
    def test_clean_content(self, converter):
        """Test de nettoyage du contenu"""
        # Contenu avec caractères de contrôle et lignes longues
        dirty_content = "Normal text\x00\x01\x02\nVery long line that exceeds the maximum length limit and should be split into multiple lines for better readability in the PDF document"
        
        cleaned = converter._clean_content(dirty_content)
        
        assert '\x00' not in cleaned
        assert '\x01' not in cleaned
        assert '\x02' not in cleaned
        # Vérification que les lignes longues sont découpées
        lines = cleaned.split('\n')
        for line in lines:
            assert len(line) <= 100 or ' ' not in line  # Sauf si c'est un mot unique très long
    
    def test_clean_content_empty(self, converter):
        """Test de nettoyage de contenu vide"""
        result = converter._clean_content("")
        assert result == ""
        
        result = converter._clean_content(None)
        assert result == ""
    
    def test_format_date(self, converter):
        """Test de formatage de date"""
        from datetime import datetime
        
        # Date datetime
        date_obj = datetime(2023, 1, 15, 14, 30, 45)
        result = converter._format_date(date_obj)
        assert result == "15/01/2023 14:30:45"
        
        # Date string
        result = converter._format_date("2023-01-15")
        assert result == "2023-01-15"
        
        # Date None
        result = converter._format_date(None)
        assert result == "Non spécifiée"
        
        # Date invalide
        result = converter._format_date(12345)
        assert result == "12345"
    
    def test_process_attachments_no_attachments(self, converter, mock_extract_msg):
        """Test de traitement sans pièces jointes"""
        request_id = "test-request-123"
        mock_extract_msg.attachments = []
        
        result = converter._process_attachments(mock_extract_msg, request_id)
        
        assert result == []
    
    def test_process_attachments_with_pdf(self, converter, mock_extract_msg):
        """Test de traitement avec pièces jointes PDF"""
        request_id = "test-request-123"
        
        # Mock d'une pièce jointe PDF
        mock_attachment = Mock()
        mock_attachment.longFilename = "document.pdf"
        mock_attachment.shortFilename = "doc.pdf"
        mock_attachment.data = b"PDF attachment data"
        
        mock_extract_msg.attachments = [mock_attachment]
        
        result = converter._process_attachments(mock_extract_msg, request_id)
        
        assert len(result) == 1
        assert result[0] == b"PDF attachment data"
    
    def test_process_attachments_non_pdf(self, converter, mock_extract_msg):
        """Test de traitement avec pièces jointes non-PDF"""
        request_id = "test-request-123"
        
        # Mock d'une pièce jointe non-PDF
        mock_attachment = Mock()
        mock_attachment.longFilename = "document.docx"
        mock_attachment.shortFilename = "doc.docx"
        mock_attachment.data = b"Word document data"
        
        mock_extract_msg.attachments = [mock_attachment]
        
        result = converter._process_attachments(mock_extract_msg, request_id)
        
        assert len(result) == 0  # Les fichiers non-PDF sont ignorés
    
    def test_process_attachments_mixed(self, converter, mock_extract_msg):
        """Test de traitement avec pièces jointes mixtes"""
        request_id = "test-request-123"
        
        # Mock de pièces jointes mixtes
        pdf_attachment = Mock()
        pdf_attachment.longFilename = "document.pdf"
        pdf_attachment.data = b"PDF data"
        
        word_attachment = Mock()
        word_attachment.longFilename = "document.docx"
        word_attachment.data = b"Word data"
        
        mock_extract_msg.attachments = [pdf_attachment, word_attachment]
        
        result = converter._process_attachments(mock_extract_msg, request_id)
        
        assert len(result) == 1  # Seul le PDF est traité
        assert result[0] == b"PDF data"
    
    def test_merge_pdfs_no_attachments(self, converter):
        """Test de fusion sans pièces jointes"""
        request_id = "test-request-123"
        main_pdf = b"Main PDF content"
        attachment_pdfs = []
        
        result = converter.merge_pdfs(main_pdf, attachment_pdfs, request_id)
        
        assert result == main_pdf
    
    def test_merge_pdfs_with_attachments(self, converter, sample_pdf_content):
        """Test de fusion avec pièces jointes"""
        request_id = "test-request-123"
        main_pdf = sample_pdf_content
        attachment_pdfs = [sample_pdf_content]
        
        with patch('app.services.msg_converter.PdfReader') as mock_reader, \
             patch('app.services.msg_converter.PdfWriter') as mock_writer:
            
            # Configuration des mocks
            mock_page = Mock()
            mock_reader_instance = Mock()
            mock_reader_instance.pages = [mock_page]
            mock_reader.return_value = mock_reader_instance
            
            mock_writer_instance = Mock()
            mock_writer.return_value = mock_writer_instance
            
            # Mock du buffer de sortie
            output_buffer = io.BytesIO(b"Merged PDF content")
            with patch('io.BytesIO') as mock_bytesio:
                mock_bytesio.return_value = output_buffer
                
                result = converter.merge_pdfs(main_pdf, attachment_pdfs, request_id)
                
                # Vérification que les pages ont été ajoutées
                assert mock_writer_instance.add_page.call_count >= 2  # Au moins main + attachment
    
    def test_merge_pdfs_error(self, converter):
        """Test d'erreur lors de la fusion"""
        request_id = "test-request-123"
        main_pdf = b"Invalid PDF"
        attachment_pdfs = [b"Invalid attachment PDF"]
        
        with patch('app.services.msg_converter.PdfReader') as mock_reader:
            mock_reader.side_effect = Exception("Invalid PDF format")
            
            with pytest.raises(MSGConversionError, match="Erreur de fusion"):
                converter.merge_pdfs(main_pdf, attachment_pdfs, request_id)
    
    def test_create_metadata_table(self, converter, mock_extract_msg):
        """Test de création du tableau de métadonnées"""
        table = converter._create_metadata_table(mock_extract_msg)
        
        assert table is not None
        # Vérification que la table contient les bonnes données
        # (Les détails dépendent de l'implémentation de ReportLab)