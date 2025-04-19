#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaire pour la génération des clips à partir des vidéos YouTube.
Ce module adapte le script bot_clip.py original en une API utilisable.
"""

import os
import random
import subprocess
import tempfile
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_clip(youtube_url, mode='short', transitions=True):
    """
    Génère un clip à partir d'une vidéo YouTube.
    
    Args:
        youtube_url: URL de la vidéo YouTube
        mode: Mode de génération ('short' ou 'long')
        transitions: Booléen indiquant si les transitions doivent être ajoutées
        
    Returns:
        Chemin du fichier clip généré
        
    Raises:
        ValueError: Si le mode n'est pas valide ou si la génération échoue
    """
    if mode not in ['short', 'long']:
        raise ValueError("Mode invalide. Utilisez 'short' ou 'long'.")
    
    # Création d'un répertoire temporaire pour les fichiers de travail
    temp_dir = tempfile.mkdtemp()
    output_file = os.path.join(temp_dir, f"clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
    
    try:
        # Téléchargement de la vidéo
        logger.info(f"Téléchargement de la vidéo: {youtube_url}")
        video_path = _download_video(youtube_url, temp_dir)
        
        # Obtention de la durée de la vidéo
        video_duration = _get_video_duration(video_path)
        logger.info(f"Durée de la vidéo: {video_duration} secondes")
        
        # Détection des segments populaires
        if mode == 'short':
            segments = _detect_short_segments(video_path)
        else:
            segments = _detect_long_segments(video_path, video_duration)
        
        # Génération du clip
        logger.info(f"Génération du clip en mode {mode} avec {len(segments)} segments")
        _create_clip(video_path, segments, output_file, transitions)
        
        return output_file
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération du clip: {str(e)}")
        # Nettoyage des fichiers temporaires en cas d'erreur
        _cleanup(temp_dir)
        raise ValueError(f"Erreur lors de la génération du clip: {str(e)}")

def _download_video(youtube_url, output_dir):
    """
    Télécharge une vidéo YouTube.
    
    Args:
        youtube_url: URL de la vidéo YouTube
        output_dir: Répertoire de sortie
        
    Returns:
        Chemin du fichier vidéo téléchargé
    """
    output_template = os.path.join(output_dir, "video.%(ext)s")
    
    cmd = [
        'youtube-dl',
        '--format', 'best[ext=mp4]',
        '--output', output_template,
        youtube_url
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Recherche du fichier téléchargé
        for file in os.listdir(output_dir):
            if file.startswith("video."):
                return os.path.join(output_dir, file)
        
        raise ValueError("Fichier vidéo non trouvé après téléchargement")
    
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Erreur lors du téléchargement de la vidéo: {e.stderr.decode('utf-8')}")

def _get_video_duration(video_path):
    """
    Obtient la durée d'une vidéo en secondes.
    
    Args:
        video_path: Chemin du fichier vidéo
        
    Returns:
        Durée de la vidéo en secondes
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Erreur lors de l'obtention de la durée de la vidéo: {e.stderr}")
    except ValueError:
        raise ValueError("Impossible de convertir la durée en nombre")

def _detect_short_segments(video_path):
    """
    Détecte les segments populaires pour un clip court.
    
    Args:
        video_path: Chemin du fichier vidéo
        
    Returns:
        Liste des segments (tuples de début et fin en secondes)
    """
    # Pour un clip court, on choisit une durée aléatoire entre 30 et 60 secondes
    clip_duration = random.randint(30, 60)
    
    # Simulation de la détection des segments populaires
    # Dans une implémentation réelle, on utiliserait l'algorithme de détection
    # des moments populaires du script original
    
    # Pour l'instant, on prend simplement un segment aléatoire dans la vidéo
    video_duration = _get_video_duration(video_path)
    
    # On s'assure que le segment ne dépasse pas la durée de la vidéo
    if clip_duration >= video_duration:
        start_time = 0
        end_time = video_duration
    else:
        max_start_time = video_duration - clip_duration
        start_time = random.uniform(0, max_start_time)
        end_time = start_time + clip_duration
    
    return [(start_time, end_time)]

def _detect_long_segments(video_path, video_duration):
    """
    Détecte les segments populaires pour un clip long.
    
    Args:
        video_path: Chemin du fichier vidéo
        video_duration: Durée de la vidéo en secondes
        
    Returns:
        Liste des segments (tuples de début et fin en secondes)
    """
    # Pour un clip long, on vise 20% de la durée totale
    target_duration = video_duration * 0.2
    
    # Durées possibles pour les segments (en secondes)
    segment_durations = [30, 60, 120, 180, 300]
    
    # Simulation de la détection des segments populaires
    # Dans une implémentation réelle, on utiliserait l'algorithme de détection
    # des moments populaires du script original
    
    segments = []
    current_duration = 0
    
    while current_duration < target_duration:
        # Choix aléatoire d'une durée de segment
        duration = random.choice(segment_durations)
        
        # Si on dépasse la cible avec ce segment, on ajuste
        if current_duration + duration > target_duration:
            duration = target_duration - current_duration
        
        # Si la durée restante est trop courte, on arrête
        if duration < 10:
            break
        
        # Choix aléatoire d'un moment de début
        max_start_time = video_duration - duration
        start_time = random.uniform(0, max_start_time)
        end_time = start_time + duration
        
        # Ajout du segment
        segments.append((start_time, end_time))
        current_duration += duration
    
    return segments

def _create_clip(video_path, segments, output_file, transitions=True):
    """
    Crée un clip à partir des segments spécifiés.
    
    Args:
        video_path: Chemin du fichier vidéo source
        segments: Liste des segments (tuples de début et fin en secondes)
        output_file: Chemin du fichier de sortie
        transitions: Booléen indiquant si les transitions doivent être ajoutées
    """
    # Création d'un fichier temporaire pour la liste des segments
    temp_dir = os.path.dirname(output_file)
    segments_file = os.path.join(temp_dir, "segments.txt")
    
    with open(segments_file, 'w') as f:
        for i, (start, end) in enumerate(segments):
            # Format: fichier_entrée|début|fin|fichier_sortie
            f.write(f"file '{video_path}'\n")
            f.write(f"inpoint {start}\n")
            f.write(f"outpoint {end}\n")
    
    # Commande FFmpeg pour créer le clip
    cmd = [
        'ffmpeg',
        '-y',  # Écrase le fichier de sortie s'il existe
        '-f', 'concat',
        '-safe', '0',
        '-i', segments_file,
        '-c', 'copy'
    ]
    
    # Ajout des transitions si demandé
    if transitions and len(segments) > 1:
        # Dans une implémentation réelle, on ajouterait des transitions
        # Pour l'instant, on utilise simplement une copie directe
        pass
    
    # Ajout du fichier de sortie
    cmd.append(output_file)
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Erreur lors de la création du clip: {e.stderr.decode('utf-8')}")
    
    finally:
        # Nettoyage du fichier de segments
        if os.path.exists(segments_file):
            os.remove(segments_file)

def _cleanup(directory):
    """
    Nettoie les fichiers temporaires.
    
    Args:
        directory: Répertoire à nettoyer
    """
    try:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        os.rmdir(directory)
    
    except Exception as e:
        logger.warning(f"Erreur lors du nettoyage des fichiers temporaires: {str(e)}")
