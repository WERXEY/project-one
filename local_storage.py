#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion du stockage local des clips générés.
"""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Répertoire de stockage des clips
STORAGE_DIR = os.environ.get('CLIPS_STORAGE_DIR', '/home/ubuntu/clips_storage')

def init_storage():
    """
    Initialise le répertoire de stockage.
    """
    os.makedirs(STORAGE_DIR, exist_ok=True)
    logger.info(f"Répertoire de stockage initialisé: {STORAGE_DIR}")

def save_clip(source_path, clip_id):
    """
    Sauvegarde un clip dans le stockage local.
    
    Args:
        source_path: Chemin du fichier source
        clip_id: Identifiant unique du clip
        
    Returns:
        Chemin du fichier sauvegardé
    """
    # Création du répertoire de stockage s'il n'existe pas
    init_storage()
    
    # Création d'un sous-répertoire pour le clip
    clip_dir = os.path.join(STORAGE_DIR, clip_id)
    os.makedirs(clip_dir, exist_ok=True)
    
    # Détermination du nom de fichier
    file_extension = Path(source_path).suffix
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"clip_{timestamp}{file_extension}"
    
    # Chemin complet du fichier de destination
    dest_path = os.path.join(clip_dir, filename)
    
    # Copie du fichier
    try:
        shutil.copy2(source_path, dest_path)
        logger.info(f"Clip sauvegardé: {dest_path}")
        return dest_path
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du clip: {str(e)}")
        raise ValueError(f"Erreur lors de la sauvegarde du clip: {str(e)}")

def get_clip_path(clip_id, filename=None):
    """
    Récupère le chemin d'un clip stocké.
    
    Args:
        clip_id: Identifiant unique du clip
        filename: Nom du fichier (si None, retourne le premier fichier trouvé)
        
    Returns:
        Chemin du fichier ou None si non trouvé
    """
    clip_dir = os.path.join(STORAGE_DIR, clip_id)
    
    if not os.path.exists(clip_dir):
        logger.warning(f"Répertoire du clip non trouvé: {clip_dir}")
        return None
    
    if filename:
        # Si un nom de fichier est spécifié, on cherche ce fichier
        file_path = os.path.join(clip_dir, filename)
        return file_path if os.path.exists(file_path) else None
    else:
        # Sinon, on retourne le premier fichier trouvé
        files = [f for f in os.listdir(clip_dir) if os.path.isfile(os.path.join(clip_dir, f))]
        return os.path.join(clip_dir, files[0]) if files else None

def delete_clip(clip_id):
    """
    Supprime un clip du stockage.
    
    Args:
        clip_id: Identifiant unique du clip
        
    Returns:
        True si la suppression a réussi, False sinon
    """
    clip_dir = os.path.join(STORAGE_DIR, clip_id)
    
    if not os.path.exists(clip_dir):
        logger.warning(f"Répertoire du clip non trouvé: {clip_dir}")
        return False
    
    try:
        shutil.rmtree(clip_dir)
        logger.info(f"Clip supprimé: {clip_id}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du clip: {str(e)}")
        return False

def list_clips():
    """
    Liste tous les clips stockés.
    
    Returns:
        Liste des identifiants de clips
    """
    if not os.path.exists(STORAGE_DIR):
        return []
    
    return [d for d in os.listdir(STORAGE_DIR) if os.path.isdir(os.path.join(STORAGE_DIR, d))]

def get_storage_info():
    """
    Récupère des informations sur le stockage.
    
    Returns:
        Dictionnaire contenant des informations sur le stockage
    """
    if not os.path.exists(STORAGE_DIR):
        return {
            'path': STORAGE_DIR,
            'exists': False,
            'clips_count': 0,
            'total_size': 0
        }
    
    clips = list_clips()
    total_size = 0
    
    for clip_id in clips:
        clip_dir = os.path.join(STORAGE_DIR, clip_id)
        for file in os.listdir(clip_dir):
            file_path = os.path.join(clip_dir, file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    
    return {
        'path': STORAGE_DIR,
        'exists': True,
        'clips_count': len(clips),
        'total_size': total_size
    }
