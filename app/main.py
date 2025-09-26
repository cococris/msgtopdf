"""
Application FastAPI principale
"""
import os
import tempfile
import uuid
import time
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.logging_config import setup_logging, get_logger, log_request_info, log_conversion_info, log_error
from app.auth import get_current_user, get_user_id, JWTError
from app.models import ConversionResponse, ErrorResponse, HealthResponse, UserInfo
from app.services.msg_converter import MSGConverter, MSGConversionError, UnauthorizedAttachmentError

# Configuration du logging
setup_logging()
logger = get_logger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À configurer selon vos besoins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de sécurité
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # À configurer selon vos besoins
)

# Instance du convertisseur
converter = MSGConverter()


@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application"""
    logger.info("Démarrage de l'API MSG to PDF Converter")
    logger.info(f"Version: {settings.api_version}")
    logger.info(f"JWKS URL: {settings.jwks_url}")
    
    # Vérification de la connectivité JWKS au démarrage
    try:
        from app.auth import get_jwks
        get_jwks()
        logger.info("Connexion JWKS vérifiée")
    except Exception as e:
        logger.warning(f"Problème de connexion JWKS: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt de l'application"""
    logger.info("Arrêt de l'API MSG to PDF Converter")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Point de contrôle de santé de l'API"""
    jwks_status = "ok"
    try:
        from app.auth import get_jwks
        get_jwks()
    except Exception:
        jwks_status = "error"
    
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        jwks_status=jwks_status
    )


@app.get("/user/info", response_model=UserInfo, tags=["User"])
async def get_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur connecté"""
    from app.auth import get_user_email, get_user_roles
    
    return UserInfo(
        user_id=get_user_id(current_user),
        email=get_user_email(current_user),
        roles=get_user_roles(current_user),
        token_exp=datetime.fromtimestamp(current_user.get("exp", 0)) if current_user.get("exp") else None
    )


@app.post("/convert", response_model=ConversionResponse, tags=["Conversion"])
async def convert_msg_to_pdf(
    file: UploadFile = File(..., description="Fichier .msg à convertir"),
    merge_attachments: bool = Form(default=True, description="Fusionner les PDFs et images en pièces jointes"),
    strict_mode: bool = Form(default=False, description="Mode strict: refuse la conversion si des pièces jointes non autorisées sont présentes"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Convertit un fichier .msg Outlook en PDF
    
    - **file**: Fichier .msg à convertir (obligatoire)
    - **merge_attachments**: Si True, fusionne les PDFs et images en pièces jointes avec le mail converti
    - **strict_mode**: Si True, refuse la conversion si le message contient des pièces jointes non autorisées
    
    **Pièces jointes autorisées :** PDFs et images (JPG, PNG, GIF, BMP, TIFF, WebP)
    
    Retourne le PDF converti avec les métadonnées de conversion.
    """
    request_id = str(uuid.uuid4())
    user_id = get_user_id(current_user)
    start_time = time.time()
    
    log_request_info(request_id, "/convert", "POST", user_id)
    
    # Validation du fichier
    if not file.filename:
        error_msg = "Nom de fichier manquant"
        log_error(request_id, ValueError(error_msg))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    if not file.filename.lower().endswith('.msg'):
        error_msg = f"Type de fichier non supporté: {file.filename}. Seuls les fichiers .msg sont acceptés."
        log_error(request_id, ValueError(error_msg))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Vérification de la taille du fichier
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > settings.max_file_size:
        error_msg = f"Fichier trop volumineux: {file_size} bytes. Limite: {settings.max_file_size} bytes"
        log_error(request_id, ValueError(error_msg))
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_msg
        )
    
    temp_file_path = None
    try:
        # Sauvegarde temporaire du fichier
        with tempfile.NamedTemporaryFile(delete=False, suffix='.msg') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        logger.info(f"[{request_id}] Fichier temporaire créé: {temp_file_path}")
        
        # Conversion
        main_pdf, attachment_pdfs = converter.convert_msg_to_pdf(temp_file_path, request_id, strict_mode)
        
        logger.info(f"[{request_id}] PDF principal créé: {len(main_pdf)} bytes")
        logger.info(f"[{request_id}] Pièces jointes PDF trouvées: {len(attachment_pdfs)}")
        
        # Fusion si demandée
        if merge_attachments:
            if attachment_pdfs:
                logger.info(f"[{request_id}] Fusion de {len(attachment_pdfs)} PDF(s) avec le mail principal...")
                final_pdf = converter.merge_pdfs(main_pdf, attachment_pdfs, request_id)
                attachments_count = len(attachment_pdfs)
                logger.info(f"[{request_id}] Fusion terminée: {len(final_pdf)} bytes au total")
            else:
                logger.info(f"[{request_id}] Aucune pièce jointe PDF à fusionner")
                final_pdf = main_pdf
                attachments_count = 0
        else:
            logger.info(f"[{request_id}] Fusion désactivée par l'utilisateur")
            final_pdf = main_pdf
            attachments_count = 0
        
        processing_time = time.time() - start_time
        output_filename = f"{Path(file.filename).stem}.pdf"
        
        # Logging de la conversion
        log_conversion_info(request_id, file.filename, file_size, processing_time)
        
        # Préparation de la réponse
        response_data = ConversionResponse(
            request_id=request_id,
            filename=file.filename,
            output_filename=output_filename,
            file_size=file_size,
            output_size=len(final_pdf),
            processing_time=processing_time,
            attachments_processed=attachments_count,
            created_at=datetime.utcnow()
        )
        
        logger.info(f"[{request_id}] Conversion réussie - Taille finale: {len(final_pdf)} bytes")
        
        # Retour du PDF avec les métadonnées dans les headers
        return Response(
            content=final_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
                "X-Request-ID": request_id,
                "X-Processing-Time": str(processing_time),
                "X-Attachments-Processed": str(attachments_count),
                "X-Original-Size": str(file_size),
                "X-Output-Size": str(len(final_pdf))
            }
        )
        
    except UnauthorizedAttachmentError as e:
        # Erreur de pièces jointes non autorisées - code 400
        log_error(request_id, e, {"filename": file.filename, "file_size": file_size})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)  # Message direct sans préfixe
        )
    except MSGConversionError as e:
        log_error(request_id, e, {"filename": file.filename, "file_size": file_size})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur de conversion: {str(e)}"
        )
    except Exception as e:
        log_error(request_id, e, {"filename": file.filename, "file_size": file_size})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )
    finally:
        # Nettoyage du fichier temporaire
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"[{request_id}] Fichier temporaire supprimé: {temp_file_path}")
            except Exception as e:
                logger.warning(f"[{request_id}] Impossible de supprimer le fichier temporaire: {e}")


@app.exception_handler(JWTError)
async def jwt_exception_handler(request, exc: JWTError):
    """Gestionnaire d'exception pour les erreurs JWT"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(exc),
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Gestionnaire d'exception HTTP personnalisé"""
    request_id = str(uuid.uuid4())
    
    logger.warning(f"[{request_id}] HTTP Exception: {exc.status_code} - {exc.detail}")
    
    # Retourner le format standard FastAPI pour les tests
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"X-Request-ID": request_id}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Gestionnaire d'exception général"""
    request_id = str(uuid.uuid4())
    
    log_error(request_id, exc)
    
    # Retourner le format standard FastAPI pour les tests
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erreur interne du serveur"},
        headers={"X-Request-ID": request_id}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )