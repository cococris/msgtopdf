# Documentation technique : Module MSG Converter

## Vue d'ensemble

Le module `msg_converter.py` est le cœur métier de l'application. Il est responsable de la conversion des fichiers .msg (emails Outlook) en documents PDF avec gestion des pièces jointes.

## Architecture du module

### Classes principales

#### 1. `MSGConversionError`
```python
class MSGConversionError(Exception):
```
- **Rôle** : Exception personnalisée pour les erreurs de conversion
- **Usage** : Utilisée pour encapsuler toutes les erreurs liées à la conversion MSG

#### 2. `UnauthorizedAttachmentError`
```python
class UnauthorizedAttachmentError(MSGConversionError):
```
- **Rôle** : Exception spécialisée pour les pièces jointes non autorisées
- **Usage** : Levée en mode strict quand des fichiers non supportés sont détectés

#### 3. `MSGConverter` (Classe principale)
Service principal de conversion avec toute la logique métier.

## Fonctionnalités principales

### 1. Conversion MSG → PDF
**Méthode** : `convert_msg_to_pdf()`

**Processus** :
1. **Extraction** du message avec `extract_msg`
2. **Validation** des pièces jointes (si mode strict activé)
3. **Création** du PDF principal contenant le mail
4. **Traitement** des pièces jointes (conversion images → PDF, extraction des PDFs)
5. **Retour** : Tuple (PDF principal, Liste des PDFs de pièces jointes)

### 2. Gestion des styles PDF
**Méthode** : `_setup_custom_styles()`

**Styles définis** :
- `title_style` : Titre principal (16pt, Helvetica-Bold, noir)
- `header_style` : En-têtes de sections (12pt, Helvetica-Bold, noir)
- `meta_style` : Métadonnées unifiées (10pt, Helvetica)
- `body_style` : Corps du texte (11pt, avec marges)
- `paragraph_style` : Paragraphes (11pt, espacement optimisé)

### 3. Création du PDF principal
**Méthode** : `_create_main_pdf()`

**Structure du PDF** :
```
1. Titre : "Email Outlook"
2. Métadonnées :
   - De: [expéditeur]
   - À: [destinataires]
   - CC: [copie carbone]
   - Objet: [sujet]
   - Date: [date formatée]
3. Contenu du message
4. Tableau des pièces jointes (si présentes)
```

### 4. Traitement des métadonnées
**Méthode** : `_add_metadata_section()`

**Format unifié** :
- **Avant** : Labels et valeurs sur lignes séparées avec indentation
- **Après** : Format `<b>Label:</b> valeur` sur une seule ligne
- **Avantage** : Plus compact et lisible, comme un email classique

### 5. Gestion des pièces jointes
**Méthode** : `_process_attachments()`

**Types supportés** :
- **PDFs** : Ajoutés directement à la fusion
- **Images** : JPG, PNG, GIF, BMP, TIFF, WebP → Converties en PDF
- **Autres** : Ignorés (ou erreur en mode strict)

**Processus pour les images** :
1. Ouverture avec `PIL` (Python Imaging Library)
2. Conversion en RGB si nécessaire
3. **Détection automatique de l'orientation** (paysage vs portrait)
4. **Adaptation du format de page** : A4 portrait ou A4 paysage selon l'image
5. Redimensionnement pour s'adapter au format choisi
6. Génération d'un PDF avec `ReportLab`
7. Ajout à la liste des PDFs à fusionner

### 6. Fusion des PDFs
**Méthode** : `merge_pdfs()`

**Processus** :
1. Création d'un `PdfWriter`
2. Ajout des pages du PDF principal
3. Ajout séquentiel des pages de chaque pièce jointe
4. Génération du PDF final fusionné

### 7. Mode strict
**Méthode** : `_validate_attachments_strict()`

**Fonctionnement** :
- Analyse toutes les pièces jointes AVANT traitement
- Lève `UnauthorizedAttachmentError` si fichiers non supportés trouvés
- Permet de refuser la conversion entière plutôt que d'ignorer des fichiers

## Améliorations apportées

### 1. Suppression des emojis
**Avant** : Logs avec emojis (🚀, ✅, ❌, 📧, etc.)
**Après** : Messages propres sans emojis
**Avantage** : Compatibilité avec tous les systèmes de logging

### 2. Simplification des styles PDF
**Avant** :
- Couleurs bleues pour titres et séparateurs
- Séparateurs colorés avec `HRFlowable`
- Tableaux avec alternance de couleurs complexe

**Après** :
- Couleurs uniquement noires
- Suppression des séparateurs graphiques
- Tableaux simples avec bordures noires
- Style uniforme comme impression d'email classique

### 3. Métadonnées unifiées
**Avant** :
```
De :
    john.doe@example.com
À :
    team@example.com
```

**Après** :
```
De: john.doe@example.com
À: team@example.com
```

### 4. Orientation adaptative des images
**Nouvelle fonctionnalité** :
- **Images paysage** (largeur > hauteur) → PDF en orientation paysage
- **Images portrait** (hauteur > largeur) → PDF en orientation portrait
- **Avantage** : Utilisation optimale de l'espace, meilleur rendu visuel

## Points techniques importants

### 1. Gestion des erreurs
- Exceptions spécialisées pour différents types d'erreurs
- Logging détaillé avec request_id pour traçabilité
- Nettoyage automatique des fichiers temporaires

### 2. Optimisations mémoire
- Utilisation de `io.BytesIO` pour éviter les fichiers temporaires
- Traitement par chunks pour les gros fichiers
- Fermeture systématique des ressources

### 3. Nettoyage du contenu
**Méthode** : `_clean_content()`
- Suppression des caractères de contrôle
- Gestion intelligente des retours à la ligne
- Découpage des lignes trop longues
- Échappement HTML pour sécurité

### 4. Compatibilité images
- Gestion de tous les modes colorimétriques (RGB, RGBA, LA, etc.)
- Fond blanc automatique pour transparence
- Redimensionnement proportionnel pour A4
- Compression JPEG optimisée

## Flux de traitement complet

```
1. Réception fichier .msg
   ↓
2. Extraction avec extract_msg
   ↓
3. [Mode strict] Validation pièces jointes
   ↓
4. Génération PDF principal (mail)
   ↓
5. Traitement pièces jointes :
   - PDFs → Extraction directe
   - Images → Conversion PDF
   - Autres → Ignoré/Erreur
   ↓
6. [Si fusion activée] Merge des PDFs
   ↓
7. Retour PDF final
```

## Configuration et paramètres

### Variables importantes :
- `settings.max_file_size` : Limite de taille des fichiers
- Formats A4 pour tous les PDFs générés
- Marges standardisées (0.7-0.8 pouces)
- Police Helvetica pour cohérence

### Extensions supportées :
- **PDFs** : `.pdf`
- **Images** : `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`

## Utilisation dans l'API

Le converter est instancié une seule fois au démarrage de l'API et réutilisé pour toutes les requêtes, optimisant les performances.

```python
# Dans main.py
converter = MSGConverter()

# Utilisation
main_pdf, attachment_pdfs = converter.convert_msg_to_pdf(
    msg_file_path, 
    request_id, 
    strict_mode
)
```

Cette architecture garantit une conversion robuste et efficace des emails Outlook en PDF avec un style épuré et professionnel.