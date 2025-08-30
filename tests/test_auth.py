"""
Tests pour le module d'authentification
"""
import pytest
from unittest.mock import patch, Mock
import jwt
import requests
from app.auth import (
    get_jwks, get_public_key, verify_jwt_token, 
    JWTError, get_user_id, get_user_email, get_user_roles
)


class TestJWKS:
    """Tests pour la gestion des clés JWKS"""
    
    def test_get_jwks_success(self, mock_jwks_response):
        """Test de récupération réussie des clés JWKS"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = get_jwks()
            
            assert result == mock_jwks_response
            mock_get.assert_called_once()
    
    def test_get_jwks_request_error(self):
        """Test d'erreur de requête JWKS"""
        # Nettoyer le cache avant le test
        import app.auth
        app.auth._jwks_cache = {}
        app.auth._cache_expiry = 0
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Connection error")
            
            with pytest.raises(JWTError, match="Impossible de récupérer les clés JWKS"):
                get_jwks()
    
    def test_get_jwks_json_error(self):
        """Test d'erreur de décodage JSON"""
        # Nettoyer le cache avant le test
        import app.auth
        app.auth._jwks_cache = {}
        app.auth._cache_expiry = 0
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with pytest.raises(JWTError, match="Format JSON invalide"):
                get_jwks()
    
    def test_get_jwks_cache(self, mock_jwks_response):
        """Test du cache JWKS"""
        # Nettoyer le cache avant le test
        import app.auth
        app.auth._jwks_cache = {}
        app.auth._cache_expiry = 0
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Premier appel
            result1 = get_jwks()
            # Deuxième appel (devrait utiliser le cache)
            result2 = get_jwks()
            
            assert result1 == result2
            # Seul le premier appel devrait faire une requête HTTP
            assert mock_get.call_count == 1


class TestPublicKey:
    """Tests pour la récupération des clés publiques"""
    
    def test_get_public_key_success(self, mock_jwks_response):
        """Test de récupération réussie d'une clé publique"""
        with patch('app.auth.get_jwks') as mock_get_jwks, \
             patch('jwt.utils.base64url_decode') as mock_decode:
            
            mock_get_jwks.return_value = mock_jwks_response
            mock_decode.side_effect = [b'test_n', b'test_e']
            
            with patch('app.auth.rsa.RSAPublicNumbers') as mock_rsa:
                mock_public_key = Mock()
                mock_public_key.public_bytes.return_value = b'-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----'
                mock_rsa.return_value.public_key.return_value = mock_public_key
                
                result = get_public_key("test-key-id")
                
                assert "BEGIN PUBLIC KEY" in result
    
    def test_get_public_key_not_found(self, mock_jwks_response):
        """Test de clé publique non trouvée"""
        with patch('app.auth.get_jwks') as mock_get_jwks:
            mock_get_jwks.return_value = mock_jwks_response
            
            with pytest.raises(JWTError, match="Clé avec kid 'unknown-key' non trouvée"):
                get_public_key("unknown-key")
    
    def test_get_public_key_unsupported_type(self):
        """Test de type de clé non supporté"""
        jwks_with_ec = {
            "keys": [
                {
                    "kty": "EC",  # Type non supporté
                    "kid": "test-key-id",
                    "use": "sig",
                    "alg": "ES256"
                }
            ]
        }
        
        with patch('app.auth.get_jwks') as mock_get_jwks:
            mock_get_jwks.return_value = jwks_with_ec
            
            with pytest.raises(JWTError, match="Type de clé non supporté: EC"):
                get_public_key("test-key-id")


class TestJWTVerification:
    """Tests pour la vérification des tokens JWT"""
    
    def test_verify_jwt_token_success(self, mock_jwt_payload):
        """Test de vérification réussie d'un token JWT"""
        with patch('jwt.get_unverified_header') as mock_header, \
             patch('app.auth.get_public_key') as mock_get_key, \
             patch('jwt.decode') as mock_decode:
            
            mock_header.return_value = {"kid": "test-key-id"}
            mock_get_key.return_value = "test-public-key"
            mock_decode.return_value = mock_jwt_payload
            
            result = verify_jwt_token("test-token")
            
            assert result == mock_jwt_payload
            mock_decode.assert_called_once()
    
    def test_verify_jwt_token_no_kid(self):
        """Test de token sans kid dans l'en-tête"""
        with patch('jwt.get_unverified_header') as mock_header:
            mock_header.return_value = {}  # Pas de kid
            
            with pytest.raises(JWTError, match="Token JWT sans 'kid'"):
                verify_jwt_token("test-token")
    
    def test_verify_jwt_token_expired(self):
        """Test de token expiré"""
        with patch('jwt.get_unverified_header') as mock_header, \
             patch('app.auth.get_public_key') as mock_get_key, \
             patch('jwt.decode') as mock_decode:
            
            mock_header.return_value = {"kid": "test-key-id"}
            mock_get_key.return_value = "test-public-key"
            mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")
            
            with pytest.raises(JWTError, match="Token expiré"):
                verify_jwt_token("test-token")
    
    def test_verify_jwt_token_invalid(self):
        """Test de token invalide"""
        with patch('jwt.get_unverified_header') as mock_header, \
             patch('app.auth.get_public_key') as mock_get_key, \
             patch('jwt.decode') as mock_decode:
            
            mock_header.return_value = {"kid": "test-key-id"}
            mock_get_key.return_value = "test-public-key"
            mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")
            
            with pytest.raises(JWTError, match="Token invalide"):
                verify_jwt_token("test-token")


class TestUserExtraction:
    """Tests pour l'extraction des informations utilisateur"""
    
    def test_get_user_id(self, mock_jwt_payload):
        """Test d'extraction de l'ID utilisateur"""
        result = get_user_id(mock_jwt_payload)
        assert result == "test-user-123"
    
    def test_get_user_id_missing(self):
        """Test d'extraction d'ID utilisateur manquant"""
        payload = {}
        result = get_user_id(payload)
        assert result == "unknown"
    
    def test_get_user_email(self, mock_jwt_payload):
        """Test d'extraction de l'email utilisateur"""
        result = get_user_email(mock_jwt_payload)
        assert result == "test@example.com"
    
    def test_get_user_email_missing(self):
        """Test d'extraction d'email manquant"""
        payload = {"sub": "test-user"}
        result = get_user_email(payload)
        assert result is None
    
    def test_get_user_roles(self, mock_jwt_payload):
        """Test d'extraction des rôles utilisateur"""
        result = get_user_roles(mock_jwt_payload)
        assert result == ["user"]
    
    def test_get_user_roles_missing(self):
        """Test d'extraction de rôles manquants"""
        payload = {"sub": "test-user"}
        result = get_user_roles(payload)
        assert result == []