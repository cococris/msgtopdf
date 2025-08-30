"""
Module d'authentification JWT avec JWKS
"""
import jwt
import requests
from typing import Dict, Any, Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json
import time
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)
security = HTTPBearer(auto_error=not settings.disable_auth)

# Cache pour les clés JWKS
_jwks_cache = {}
_cache_expiry = 0
CACHE_DURATION = 3600  # 1 heure


class JWTError(Exception):
    """Exception personnalisée pour les erreurs JWT"""
    pass


def get_jwks() -> Dict[str, Any]:
    """Récupère les clés JWKS depuis l'URL configurée"""
    global _jwks_cache, _cache_expiry
    
    current_time = time.time()
    
    # Vérifier le cache
    if _jwks_cache and current_time < _cache_expiry:
        logger.debug("Utilisation du cache JWKS")
        return _jwks_cache
    
    try:
        logger.info(f"Récupération des clés JWKS depuis {settings.jwks_url}")
        response = requests.get(settings.jwks_url, timeout=10)
        response.raise_for_status()
        
        try:
            jwks_data = response.json()
        except ValueError as e:
            logger.error(f"Format JSON invalide dans la réponse JWKS: {e}")
            raise JWTError("Format JSON invalide dans la réponse JWKS")
        _jwks_cache = jwks_data
        _cache_expiry = current_time + CACHE_DURATION
        
        logger.info(f"Clés JWKS récupérées avec succès ({len(jwks_data.get('keys', []))} clés)")
        return jwks_data
        
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la récupération des clés JWKS: {e}")
        raise JWTError(f"Impossible de récupérer les clés JWKS: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Erreur de décodage JSON des clés JWKS: {e}")
        raise JWTError(f"Format JSON invalide pour les clés JWKS: {e}")


def get_public_key(kid: str) -> str:
    """Récupère la clé publique correspondant au kid"""
    jwks = get_jwks()
    
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            try:
                # Conversion de la clé JWK en clé publique PEM
                if key.get("kty") == "RSA":
                    n = jwt.utils.base64url_decode(key["n"])
                    e = jwt.utils.base64url_decode(key["e"])
                    
                    # Conversion des bytes en entiers
                    n_int = int.from_bytes(n, byteorder='big')
                    e_int = int.from_bytes(e, byteorder='big')
                    
                    # Création de la clé publique RSA
                    public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
                    
                    # Sérialisation en PEM
                    pem = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                    
                    logger.debug(f"Clé publique trouvée pour kid: {kid}")
                    return pem.decode('utf-8')
                else:
                    raise JWTError(f"Type de clé non supporté: {key.get('kty')}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de la conversion de la clé JWK: {e}")
                raise JWTError(f"Erreur lors de la conversion de la clé: {e}")
    
    raise JWTError(f"Clé avec kid '{kid}' non trouvée")


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Vérifie et décode un token JWT"""
    try:
        # Décodage de l'en-tête pour récupérer le kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise JWTError("Token JWT sans 'kid' dans l'en-tête")
        
        # Récupération de la clé publique
        public_key = get_public_key(kid)
        
        # Vérification et décodage du token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"verify_exp": True}
        )
        
        logger.debug(f"Token JWT vérifié avec succès pour l'utilisateur: {payload.get('sub', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expiré")
        raise JWTError("Token expiré")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token JWT invalide: {e}")
        raise JWTError(f"Token invalide: {e}")
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token JWT: {e}")
        raise JWTError(f"Erreur de vérification: {e}")


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Dépendance FastAPI pour récupérer l'utilisateur actuel"""
    
    # Mode développement sans authentification
    if settings.disable_auth:
        logger.info("Mode développement : authentification désactivée")
        return {
            "sub": "dev-user-123",
            "email": "dev@example.com",
            "roles": ["user", "admin"],
            "exp": 9999999999,
            "iss": "dev-mode",
            "aud": "dev-api"
        }
    
    # Mode production avec authentification
    if not credentials:
        logger.warning("Token d'authentification manquant")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification requis",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        return payload
        
    except JWTError as e:
        logger.warning(f"Authentification échouée: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'authentification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def get_user_id(user: Dict[str, Any]) -> str:
    """Extrait l'ID utilisateur du payload JWT"""
    return user.get("sub", "unknown")


def get_user_email(user: Dict[str, Any]) -> Optional[str]:
    """Extrait l'email utilisateur du payload JWT"""
    return user.get("email")


def get_user_roles(user: Dict[str, Any]) -> list:
    """Extrait les rôles utilisateur du payload JWT"""
    return user.get("roles", [])