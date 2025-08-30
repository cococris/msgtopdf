"""
Générateur de JWT pour les tests en développement local
"""
import jwt
import json
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_rsa_keypair():
    """Génère une paire de clés RSA pour les tests"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    public_key = private_key.public_key()
    
    # Sérialisation des clés
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem


def create_test_jwt(user_id="test-user-123", email="test@example.com", roles=None):
    """Crée un JWT de test valide"""
    if roles is None:
        roles = ["user"]
    
    # Génération des clés
    private_key, public_key = generate_rsa_keypair()
    
    # Payload du JWT
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "iss": "dev-test-issuer",
        "aud": "dev-test-audience",
        "exp": datetime.utcnow() + timedelta(hours=24),  # Expire dans 24h
        "iat": datetime.utcnow(),
        "nbf": datetime.utcnow()
    }
    
    # Création du JWT
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": "dev-test-key"})
    
    return token, private_key, public_key


def create_mock_jwks(public_key):
    """Crée un JWKS mocké pour les tests"""
    # Extraction des composants de la clé publique
    public_key_obj = serialization.load_pem_public_key(public_key, backend=default_backend())
    public_numbers = public_key_obj.public_numbers()
    
    # Conversion en base64url
    def int_to_base64url(value):
        byte_length = (value.bit_length() + 7) // 8
        value_bytes = value.to_bytes(byte_length, byteorder='big')
        return jwt.utils.base64url_encode(value_bytes).decode('ascii')
    
    n = int_to_base64url(public_numbers.n)
    e = int_to_base64url(public_numbers.e)
    
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "dev-test-key",
                "use": "sig",
                "alg": "RS256",
                "n": n,
                "e": e
            }
        ]
    }
    
    return jwks


def main():
    """Génère un JWT et les clés pour les tests"""
    print("🔑 Génération d'un JWT de test...")
    
    # Génération du JWT
    token, private_key, public_key = create_test_jwt()
    
    # Génération du JWKS
    jwks = create_mock_jwks(public_key)
    
    print("\n" + "="*80)
    print("🎫 JWT TOKEN (à utiliser dans Authorization: Bearer <token>)")
    print("="*80)
    print(token)
    
    print("\n" + "="*80)
    print("🔐 JWKS (à servir sur votre endpoint JWKS)")
    print("="*80)
    print(json.dumps(jwks, indent=2))
    
    print("\n" + "="*80)
    print("📝 INSTRUCTIONS D'UTILISATION")
    print("="*80)
    print("1. Copiez le JWT ci-dessus")
    print("2. Utilisez-le dans vos requêtes : Authorization: Bearer <token>")
    print("3. Pour un serveur JWKS local, sauvegardez le JWKS dans un fichier")
    print("4. Ou utilisez le mode développement sans authentification")
    
    # Sauvegarde dans des fichiers
    with open("dev_jwt_token.txt", "w") as f:
        f.write(token)
    
    with open("dev_jwks.json", "w") as f:
        json.dump(jwks, f, indent=2)
    
    print("\n✅ Fichiers sauvegardés :")
    print("   - dev_jwt_token.txt : Token JWT")
    print("   - dev_jwks.json : Clés JWKS")


if __name__ == "__main__":
    main()