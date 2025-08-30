#!/usr/bin/env python3
"""
Script de démarrage de l'API MSG to PDF Converter
"""
import uvicorn
import sys
import os
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.config import settings
from app.logging_config import setup_logging

def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage de l'API MSG to PDF Converter")
    print(f"📁 Répertoire de travail: {root_dir}")
    print(f"🔧 Configuration JWKS: {settings.jwks_url}")
    print(f"📊 Niveau de log: {settings.log_level}")
    print("=" * 50)
    
    # Configuration du logging
    setup_logging()
    
    # Démarrage du serveur
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True
    )

if __name__ == "__main__":
    main()