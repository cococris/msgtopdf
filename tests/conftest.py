"""
Configuration des tests pytest
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Configuration pour désactiver le mode dev pendant les tests
os.environ["DISABLE_AUTH"] = "false"
os.environ["DEV_MODE"] = "false"

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


@pytest.fixture
def mock_jwt_payload():
    """Payload JWT mocké pour les tests"""
    return {
        "sub": "test-user-123",
        "email": "test@example.com",
        "roles": ["user"],
        "exp": 9999999999,  # Expiration très lointaine
        "iss": "test-issuer",
        "aud": "test-audience"
    }


@pytest.fixture
def mock_jwks_response():
    """Réponse JWKS mockée"""
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key-id",
                "use": "sig",
                "alg": "RS256",
                "n": "test-n-value",
                "e": "AQAB"
            }
        ]
    }


@pytest.fixture
def temp_msg_file():
    """Fichier .msg temporaire pour les tests"""
    with tempfile.NamedTemporaryFile(suffix='.msg', delete=False) as f:
        # Contenu minimal d'un fichier .msg (simulé)
        f.write(b"MSG file content for testing")
        temp_path = f.name
    
    yield temp_path
    
    # Nettoyage
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_msg_converter():
    """Convertisseur MSG mocké"""
    with patch('app.services.msg_converter.MSGConverter') as mock:
        converter_instance = Mock()
        mock.return_value = converter_instance
        
        # Configuration des méthodes mockées
        converter_instance.convert_msg_to_pdf.return_value = (
            b"PDF content",  # PDF principal
            [b"Attachment PDF content"]  # PDFs des pièces jointes
        )
        converter_instance.merge_pdfs.return_value = b"Merged PDF content"
        
        yield converter_instance


@pytest.fixture
def mock_auth():
    """Authentification mockée"""
    with patch('app.auth.verify_jwt_token') as mock_verify, \
         patch('app.auth.get_jwks') as mock_jwks:
        
        mock_verify.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "roles": ["user"],
            "exp": 9999999999
        }
        
        mock_jwks.return_value = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "test-key-id",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "test-n-value",
                    "e": "AQAB"
                }
            ]
        }
        
        yield mock_verify


@pytest.fixture
def auth_headers():
    """Headers d'authentification pour les tests"""
    return {"Authorization": "Bearer test-jwt-token"}


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configuration automatique de l'environnement de test"""
    # Sauvegarde des valeurs originales
    original_jwks_url = settings.jwks_url
    original_log_level = settings.log_level
    original_disable_auth = settings.disable_auth
    
    # Configuration pour les tests
    settings.jwks_url = "https://test-jwks.example.com/.well-known/jwks.json"
    settings.log_level = "DEBUG"
    settings.disable_auth = False  # Important : activer l'auth pour les tests
    
    # Nettoyer le cache JWKS
    import app.auth
    app.auth._jwks_cache = {}
    app.auth._cache_expiry = 0
    
    yield
    
    # Restauration des valeurs originales
    settings.jwks_url = original_jwks_url
    settings.log_level = original_log_level
    settings.disable_auth = original_disable_auth


@pytest.fixture
def sample_pdf_content():
    """Contenu PDF d'exemple pour les tests"""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"


@pytest.fixture
def mock_extract_msg():
    """Mock du module extract_msg"""
    with patch('app.services.msg_converter.extract_msg') as mock:
        # Configuration du message mocké
        mock_message = Mock()
        mock_message.sender = "sender@example.com"
        mock_message.to = "recipient@example.com"
        mock_message.cc = ""
        mock_message.subject = "Test Subject"
        mock_message.date = "2023-01-01 12:00:00"
        mock_message.body = "Test email body content"
        mock_message.attachments = []
        mock_message.close = Mock()
        
        mock.Message.return_value = mock_message
        yield mock_message