#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contrôleur pour la génération des clips.
Ce module contient la logique métier pour la génération des clips courts et longs.
"""

import uuid
import threading
from datetime import datetime
from api.utils.youtube_extractor import extract_video_info
from api.utils.clip_generator import generate_clip
from api.models.clip import Clip
from storage.local_storage import save_clip, get_clip_path

# Dictionnaire pour stocker les informations sur les clips en cours de génération
# Clé: clip_id, Valeur: dictionnaire avec les informations du clip
clips_in_progress = {}

def generate_short_clip(youtube_url, transitions=True):
    """
    Génère un clip court (30-60s) à partir d'une URL YouTube.
    
    Args:
        youtube_url: URL de la vidéo YouTube
        transitions: Booléen indiquant si les transitions doivent être ajoutées
        
    Returns:
        L'identifiant unique du clip généré
    """
    # Génération d'un identifiant unique pour le clip
    clip_id = str(uuid.uuid4())
    
    # Extraction des informations de la vidéo YouTube
    video_info = extract_video_info(youtube_url)
    
    # Création d'un objet Clip
    clip = Clip(
        id=clip_id,
        youtube_url=youtube_url,
        title=video_info['title'],
        channel=video_info['channel'],
        duration=video_info['duration'],
        mode='short',
        status='processing',
        created_at=datetime.now(),
        transitions=transitions
    )
    
    # Stockage des informations du clip
    clips_in_progress[clip_id] = clip.__dict__
    
    # Lancement de la génération du clip dans un thread séparé
    thread = threading.Thread(target=_process_short_clip, args=(clip_id, youtube_url, transitions))
    thread.daemon = True
    thread.start()
    
    return clip_id

def generate_long_clip(youtube_url, transitions=True):
    """
    Génère un clip long (20% de la durée totale) à partir d'une URL YouTube.
    
    Args:
        youtube_url: URL de la vidéo YouTube
        transitions: Booléen indiquant si les transitions doivent être ajoutées
        
    Returns:
        L'identifiant unique du clip généré
    """
    # Génération d'un identifiant unique pour le clip
    clip_id = str(uuid.uuid4())
    
    # Extraction des informations de la vidéo YouTube
    video_info = extract_video_info(youtube_url)
    
    # Création d'un objet Clip
    clip = Clip(
        id=clip_id,
        youtube_url=youtube_url,
        title=video_info['title'],
        channel=video_info['channel'],
        duration=video_info['duration'],
        mode='long',
        status='processing',
        created_at=datetime.now(),
        transitions=transitions
    )
    
    # Stockage des informations du clip
    clips_in_progress[clip_id] = clip.__dict__
    
    # Lancement de la génération du clip dans un thread séparé
    thread = threading.Thread(target=_process_long_clip, args=(clip_id, youtube_url, transitions))
    thread.daemon = True
    thread.start()
    
    return clip_id

def _process_short_clip(clip_id, youtube_url, transitions):
    """
    Fonction interne pour traiter la génération d'un clip court.
    
    Args:
        clip_id: Identifiant unique du clip
        youtube_url: URL de la vidéo YouTube
        transitions: Booléen indiquant si les transitions doivent être ajoutées
    """
    try:
        # Mise à jour du statut
        clips_in_progress[clip_id]['status'] = 'downloading'
        
        # Génération du clip
        clip_path = generate_clip(youtube_url, 'short', transitions)
        
        # Sauvegarde du clip
        file_path = save_clip(clip_path, clip_id)
        
        # Mise à jour des informations du clip
        clips_in_progress[clip_id]['status'] = 'completed'
        clips_in_progress[clip_id]['file_path'] = file_path
        clips_in_progress[clip_id]['completed_at'] = datetime.now()
        
    except Exception as e:
        # En cas d'erreur, mise à jour du statut
        clips_in_progress[clip_id]['status'] = 'failed'
        clips_in_progress[clip_id]['error'] = str(e)

def _process_long_clip(clip_id, youtube_url, transitions):
    """
    Fonction interne pour traiter la génération d'un clip long.
    
    Args:
        clip_id: Identifiant unique du clip
        youtube_url: URL de la vidéo YouTube
        transitions: Booléen indiquant si les transitions doivent être ajoutées
    """
    try:
        # Mise à jour du statut
        clips_in_progress[clip_id]['status'] = 'downloading'
        
        # Génération du clip
        clip_path = generate_clip(youtube_url, 'long', transitions)
        
        # Sauvegarde du clip
        file_path = save_clip(clip_path, clip_id)
        
        # Mise à jour des informations du clip
        clips_in_progress[clip_id]['status'] = 'completed'
        clips_in_progress[clip_id]['file_path'] = file_path
        clips_in_progress[clip_id]['completed_at'] = datetime.now()
        
    except Exception as e:
        # En cas d'erreur, mise à jour du statut
        clips_in_progress[clip_id]['status'] = 'failed'
        clips_in_progress[clip_id]['error'] = str(e)

def get_clip_status(clip_id):
    """
    Récupère le statut de génération d'un clip.
    
    Args:
        clip_id: Identifiant unique du clip
        
    Returns:
        Dictionnaire contenant le statut du clip ou None si le clip n'existe pas
    """
    if clip_id not in clips_in_progress:
        return None
    
    clip_info = clips_in_progress[clip_id]
    
    return {
        'id': clip_id,
        'status': clip_info['status'],
        'created_at': clip_info['created_at'].isoformat(),
        'completed_at': clip_info.get('completed_at', None).isoformat() if clip_info.get('completed_at') else None,
        'error': clip_info.get('error', None)
    }

def get_clip_info(clip_id):
    """
    Récupère les informations complètes d'un clip.
    
    Args:
        clip_id: Identifiant unique du clip
        
    Returns:
        Dictionnaire contenant les informations du clip ou None si le clip n'existe pas
    """
    if clip_id not in clips_in_progress:
        return None
    
    clip_info = clips_in_progress[clip_id]
    
    # Si le clip est terminé, on ajoute l'URL de téléchargement
    if clip_info['status'] == 'completed':
        clip_info['download_url'] = f"/api/clips/{clip_id}/download"
    
    return clip_info
