"""
Serveur JWKS local pour les tests de développement
"""
import json
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from jwt_generator import create_test_jwt, create_mock_jwks

# Génération des clés au démarrage
_, _, public_key = create_test_jwt()
jwks_data = create_mock_jwks(public_key)

app = FastAPI(title="Dev JWKS Server", description="Serveur JWKS pour les tests locaux")

@app.get("/.well-known/jwks.json")
async def get_jwks():
    """Endpoint JWKS pour les tests"""
    return JSONResponse(content=jwks_data)

@app.get("/")
async def root():
    """Page d'accueil du serveur JWKS"""
    return {
        "message": "Serveur JWKS de développement",
        "jwks_endpoint": "/.well-known/jwks.json",
        "status": "running"
    }

if __name__ == "__main__":
    print("🔑 Démarrage du serveur JWKS de développement...")
    print("📍 JWKS disponible sur: http://localhost:8001/.well-known/jwks.json")
    print("🔧 Configurez votre API avec: JWKS_URL=http://localhost:8001/.well-known/jwks.json")
    
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")