"""
Modèles Pydantic pour l'API
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ConversionRequest(BaseModel):
    """Modèle pour la requête de conversion"""
    merge_attachments: bool = Field(
        default=True,
        description="Indique si les PDFs en pièces jointes doivent être fusionnés"
    )


class ConversionResponse(BaseModel):
    """Modèle pour la réponse de conversion"""
    request_id: str = Field(description="Identifiant unique de la requête")
    filename: str = Field(description="Nom du fichier original")
    output_filename: str = Field(description="Nom du fichier PDF généré")
    file_size: int = Field(description="Taille du fichier original en bytes")
    output_size: int = Field(description="Taille du PDF généré en bytes")
    processing_time: float = Field(description="Temps de traitement en secondes")
    attachments_processed: int = Field(description="Nombre de pièces jointes PDF traitées")
    created_at: datetime = Field(description="Date et heure de création")


class ErrorResponse(BaseModel):
    """Modèle pour les réponses d'erreur"""
    error: str = Field(description="Type d'erreur")
    message: str = Field(description="Message d'erreur détaillé")
    request_id: Optional[str] = Field(default=None, description="Identifiant de la requête")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Horodatage de l'erreur")


class HealthResponse(BaseModel):
    """Modèle pour la réponse de santé de l'API"""
    status: str = Field(description="Statut de l'API")
    version: str = Field(description="Version de l'API")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Horodatage")
    jwks_status: str = Field(description="Statut de la connexion JWKS")


class UserInfo(BaseModel):
    """Modèle pour les informations utilisateur extraites du JWT"""
    user_id: str = Field(description="Identifiant utilisateur")
    email: Optional[str] = Field(default=None, description="Email utilisateur")
    roles: list = Field(default_factory=list, description="Rôles utilisateur")
    token_exp: Optional[datetime] = Field(default=None, description="Date d'expiration du token")