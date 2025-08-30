"""
Tests pour les endpoints de l'API
"""
import pytest
import io
from unittest.mock import patch, Mock
from fastapi import status
from app.services.msg_converter import MSGConversionError


class TestHealthEndpoint:
    """Tests pour l'endpoint de santé"""
    
    def test_health_check_success(self, client, mock_auth):
        """Test de vérification de santé réussie"""
        with patch('app.auth.get_jwks') as mock_jwks:
            mock_jwks.return_value = {"keys": []}
            
            response = client.get("/health")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            assert data["jwks_status"] == "ok"
    
    def test_health_check_jwks_error(self, client):
        """Test de vérification de santé avec erreur JWKS"""
        with patch('app.auth.get_jwks') as mock_jwks:
            mock_jwks.side_effect = Exception("JWKS error")
            
            response = client.get("/health")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "healthy"
            assert data["jwks_status"] == "error"


class TestUserInfoEndpoint:
    """Tests pour l'endpoint d'informations utilisateur"""
    
    def test_get_user_info_success(self, client, mock_auth, auth_headers):
        """Test de récupération des informations utilisateur"""
        response = client.get("/user/info", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "test@example.com"
        assert data["roles"] == ["user"]
    
    def test_get_user_info_unauthorized(self, client):
        """Test d'accès non autorisé aux informations utilisateur"""
        response = client.get("/user/info")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestConvertEndpoint:
    """Tests pour l'endpoint de conversion"""
    
    def test_convert_success(self, client, mock_auth, auth_headers, mock_msg_converter):
        """Test de conversion réussie"""
        # Préparation du fichier de test
        file_content = b"MSG file content"
        files = {"file": ("test.msg", io.BytesIO(file_content), "application/octet-stream")}
        data = {"merge_attachments": True}
        
        with patch('app.main.converter', mock_msg_converter):
            response = client.post("/convert", files=files, data=data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "application/pdf"
            assert "X-Request-ID" in response.headers
            assert "X-Processing-Time" in response.headers
            assert "X-Attachments-Processed" in response.headers
            
            # Vérification que le convertisseur a été appelé
            mock_msg_converter.convert_msg_to_pdf.assert_called_once()
            mock_msg_converter.merge_pdfs.assert_called_once()
    
    def test_convert_without_merge(self, client, mock_auth, auth_headers, mock_msg_converter):
        """Test de conversion sans fusion des pièces jointes"""
        file_content = b"MSG file content"
        files = {"file": ("test.msg", io.BytesIO(file_content), "application/octet-stream")}
        data = {"merge_attachments": False}
        
        with patch('app.main.converter', mock_msg_converter):
            response = client.post("/convert", files=files, data=data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            
            # Vérification que merge_pdfs n'a pas été appelé
            mock_msg_converter.convert_msg_to_pdf.assert_called_once()
            mock_msg_converter.merge_pdfs.assert_not_called()
    
    def test_convert_unauthorized(self, client):
        """Test de conversion sans authentification"""
        file_content = b"MSG file content"
        files = {"file": ("test.msg", io.BytesIO(file_content), "application/octet-stream")}
        
        response = client.post("/convert", files=files)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_convert_invalid_file_type(self, client, mock_auth, auth_headers):
        """Test de conversion avec type de fichier invalide"""
        file_content = b"Not a MSG file"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post("/convert", files=files, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Type de fichier non supporté" in data["detail"]
    
    def test_convert_no_filename(self, client, mock_auth, auth_headers):
        """Test de conversion sans nom de fichier"""
        file_content = b"MSG file content"
        files = {"file": ("", io.BytesIO(file_content), "application/octet-stream")}
        
        response = client.post("/convert", files=files, headers=auth_headers)
        
        # FastAPI retourne 422 pour les erreurs de validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
    
    def test_convert_file_too_large(self, client, mock_auth, auth_headers):
        """Test de conversion avec fichier trop volumineux"""
        # Création d'un fichier dépassant la limite
        large_content = b"x" * (60 * 1024 * 1024)  # 60MB > 50MB limite
        files = {"file": ("large.msg", io.BytesIO(large_content), "application/octet-stream")}
        
        response = client.post("/convert", files=files, headers=auth_headers)
        
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        data = response.json()
        assert "Fichier trop volumineux" in data["detail"]
    
    def test_convert_msg_conversion_error(self, client, mock_auth, auth_headers, mock_msg_converter):
        """Test d'erreur de conversion MSG"""
        file_content = b"Invalid MSG file"
        files = {"file": ("test.msg", io.BytesIO(file_content), "application/octet-stream")}
        
        # Configuration du mock pour lever une exception
        mock_msg_converter.convert_msg_to_pdf.side_effect = MSGConversionError("Invalid MSG format")
        
        with patch('app.main.converter', mock_msg_converter):
            response = client.post("/convert", files=files, headers=auth_headers)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            assert "Erreur de conversion" in data["detail"]
    
    def test_convert_internal_error(self, client, mock_auth, auth_headers, mock_msg_converter):
        """Test d'erreur interne lors de la conversion"""
        file_content = b"MSG file content"
        files = {"file": ("test.msg", io.BytesIO(file_content), "application/octet-stream")}
        
        # Configuration du mock pour lever une exception générique
        mock_msg_converter.convert_msg_to_pdf.side_effect = Exception("Unexpected error")
        
        with patch('app.main.converter', mock_msg_converter):
            response = client.post("/convert", files=files, headers=auth_headers)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "Erreur interne du serveur" in data["detail"]
    
    def test_convert_with_attachments(self, client, mock_auth, auth_headers, mock_msg_converter):
        """Test de conversion avec pièces jointes"""
        file_content = b"MSG file with attachments"
        files = {"file": ("test.msg", io.BytesIO(file_content), "application/octet-stream")}
        data = {"merge_attachments": True}
        
        # Configuration du mock pour retourner des pièces jointes
        mock_msg_converter.convert_msg_to_pdf.return_value = (
            b"Main PDF content",
            [b"Attachment 1 PDF", b"Attachment 2 PDF"]
        )
        mock_msg_converter.merge_pdfs.return_value = b"Merged PDF content"
        
        with patch('app.main.converter', mock_msg_converter):
            response = client.post("/convert", files=files, data=data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["X-Attachments-Processed"] == "2"
            
            # Vérification que merge_pdfs a été appelé avec les bons paramètres
            mock_msg_converter.merge_pdfs.assert_called_once_with(
                b"Main PDF content",
                [b"Attachment 1 PDF", b"Attachment 2 PDF"],
                mock_msg_converter.convert_msg_to_pdf.call_args[0][1]  # request_id
            )
    
    def test_convert_response_headers(self, client, mock_auth, auth_headers, mock_msg_converter):
        """Test des headers de réponse de conversion"""
        file_content = b"MSG file content"
        files = {"file": ("test.msg", io.BytesIO(file_content), "application/octet-stream")}
        
        with patch('app.main.converter', mock_msg_converter):
            response = client.post("/convert", files=files, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            
            # Vérification des headers
            assert "Content-Disposition" in response.headers
            assert "attachment; filename=test.pdf" in response.headers["Content-Disposition"]
            assert "X-Request-ID" in response.headers
            assert "X-Processing-Time" in response.headers
            assert "X-Attachments-Processed" in response.headers
            assert "X-Original-Size" in response.headers
            assert "X-Output-Size" in response.headers


class TestErrorHandling:
    """Tests pour la gestion des erreurs"""
    
    def test_jwt_error_handler(self, client):
        """Test du gestionnaire d'erreur JWT"""
        with patch('app.auth.verify_jwt_token') as mock_verify:
            from app.auth import JWTError
            mock_verify.side_effect = JWTError("Invalid token")
            
            response = client.get("/user/info", headers={"Authorization": "Bearer invalid-token"})
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_general_exception_handler(self, client, mock_auth, auth_headers):
        """Test du gestionnaire d'exception général"""
        with patch('app.main.converter') as mock_converter:
            mock_converter.convert_msg_to_pdf.side_effect = RuntimeError("Unexpected error")
            
            file_content = b"MSG file content"
            files = {"file": ("test.msg", io.BytesIO(file_content), "application/octet-stream")}
            
            response = client.post("/convert", files=files, headers=auth_headers)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "detail" in data
            assert "Erreur interne du serveur" in data["detail"]
            assert "X-Request-ID" in response.headers


class TestStartupShutdown:
    """Tests pour les événements de démarrage et d'arrêt"""
    
    @pytest.mark.asyncio
    async def test_startup_event_success(self):
        """Test de l'événement de démarrage réussi"""
        with patch('app.auth.get_jwks') as mock_jwks:
            mock_jwks.return_value = {"keys": []}
            
            from app.main import startup_event
            # L'événement ne devrait pas lever d'exception
            await startup_event()
    
    @pytest.mark.asyncio
    async def test_startup_event_jwks_error(self):
        """Test de l'événement de démarrage avec erreur JWKS"""
        with patch('app.auth.get_jwks') as mock_jwks:
            mock_jwks.side_effect = Exception("JWKS connection error")
            
            from app.main import startup_event
            # L'événement ne devrait pas lever d'exception même en cas d'erreur JWKS
            await startup_event()
    
    @pytest.mark.asyncio
    async def test_shutdown_event(self):
        """Test de l'événement d'arrêt"""
        from app.main import shutdown_event
        # L'événement ne devrait pas lever d'exception
        await shutdown_event()