#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèle de données pour les clips.
"""

class Clip:
    """
    Classe représentant un clip généré.
    """
    
    def __init__(self, id, youtube_url, title, channel, duration, mode, status, created_at, transitions=True):
        """
        Initialise un nouvel objet Clip.
        
        Args:
            id: Identifiant unique du clip
            youtube_url: URL de la vidéo YouTube source
            title: Titre de la vidéo
            channel: Nom de la chaîne YouTube
            duration: Durée de la vidéo originale en secondes
            mode: Mode de génération ('short' ou 'long')
            status: Statut de génération ('processing', 'downloading', 'completed', 'failed')
            created_at: Date et heure de création
            transitions: Booléen indiquant si les transitions sont activées
        """
        self.id = id
        self.youtube_url = youtube_url
        self.title = title
        self.channel = channel
        self.duration = duration
        self.mode = mode
        self.status = status
        self.created_at = created_at
        self.transitions = transitions
        self.file_path = None
        self.completed_at = None
        self.error = None
