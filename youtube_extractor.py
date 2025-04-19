#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaire pour l'extraction des informations des vidéos YouTube.
"""

import re
import subprocess
import json
from urllib.parse import urlparse, parse_qs

def extract_video_info(youtube_url):
    """
    Extrait les informations d'une vidéo YouTube.
    
    Args:
        youtube_url: URL de la vidéo YouTube
        
    Returns:
        Dictionnaire contenant les informations de la vidéo
    
    Raises:
        ValueError: Si l'URL n'est pas valide ou si la vidéo n'est pas accessible
    """
    # Validation de l'URL
    video_id = _extract_video_id(youtube_url)
    if not video_id:
        raise ValueError("URL YouTube invalide")
    
    # Utilisation de youtube-dl pour récupérer les informations de la vidéo
    try:
        cmd = [
            'youtube-dl',
            '--dump-json',
            f'https://www.youtube.com/watch?v={video_id}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        video_data = json.loads(result.stdout)
        
        # Extraction des informations pertinentes
        return {
            'id': video_data['id'],
            'title': video_data['title'],
            'channel': video_data['uploader'],
            'duration': video_data['duration'],
            'thumbnail': video_data.get('thumbnail', ''),
            'view_count': video_data.get('view_count', 0),
            'like_count': video_data.get('like_count', 0),
            'upload_date': video_data.get('upload_date', '')
        }
    
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Erreur lors de l'extraction des informations de la vidéo: {e.stderr}")
    except json.JSONDecodeError:
        raise ValueError("Impossible de décoder les informations de la vidéo")
    except KeyError as e:
        raise ValueError(f"Information manquante dans les données de la vidéo: {str(e)}")

def _extract_video_id(youtube_url):
    """
    Extrait l'identifiant de la vidéo à partir de l'URL YouTube.
    
    Args:
        youtube_url: URL de la vidéo YouTube
        
    Returns:
        Identifiant de la vidéo ou None si l'URL n'est pas valide
    """
    # Formats d'URL YouTube supportés:
    # - https://www.youtube.com/watch?v=VIDEO_ID
    # - https://youtu.be/VIDEO_ID
    # - https://www.youtube.com/embed/VIDEO_ID
    
    if not youtube_url:
        return None
    
    # Format standard: youtube.com/watch?v=VIDEO_ID
    parsed_url = urlparse(youtube_url)
    if 'youtube.com' in parsed_url.netloc and '/watch' in parsed_url.path:
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v', [None])[0]
    
    # Format court: youtu.be/VIDEO_ID
    elif 'youtu.be' in parsed_url.netloc:
        return parsed_url.path.lstrip('/')
    
    # Format embed: youtube.com/embed/VIDEO_ID
    elif 'youtube.com' in parsed_url.netloc and '/embed/' in parsed_url.path:
        return parsed_url.path.split('/embed/')[1]
    
    return None
