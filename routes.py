#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Définition des routes de l'API pour le générateur de clips "Best Of".
"""

from flask import Blueprint, request, jsonify
from api.controllers.clip_controller import generate_short_clip, generate_long_clip, get_clip_status, get_clip_info

# Création du blueprint pour l'API
api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint pour vérifier que l'API est en ligne.
    """
    return jsonify({
        'status': 'success',
        'message': 'API is running'
    }), 200

@api_bp.route('/clips', methods=['POST'])
def create_clip():
    """
    Endpoint pour créer un nouveau clip à partir d'une URL YouTube.
    
    Paramètres JSON attendus:
    - url: URL de la vidéo YouTube
    - mode: 'short' ou 'long'
    - transitions: booléen indiquant si les transitions doivent être ajoutées
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400
    
    url = data.get('url')
    mode = data.get('mode', 'short')
    transitions = data.get('transitions', True)
    
    if not url:
        return jsonify({
            'status': 'error',
            'message': 'URL is required'
        }), 400
    
    if mode not in ['short', 'long']:
        return jsonify({
            'status': 'error',
            'message': 'Mode must be either "short" or "long"'
        }), 400
    
    try:
        if mode == 'short':
            clip_id = generate_short_clip(url, transitions)
        else:
            clip_id = generate_long_clip(url, transitions)
        
        return jsonify({
            'status': 'success',
            'message': 'Clip generation started',
            'clip_id': clip_id
        }), 202
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/clips/<clip_id>', methods=['GET'])
def get_clip(clip_id):
    """
    Endpoint pour récupérer les informations d'un clip.
    """
    try:
        clip = get_clip_info(clip_id)
        
        if not clip:
            return jsonify({
                'status': 'error',
                'message': 'Clip not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'clip': clip
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/clips/<clip_id>/status', methods=['GET'])
def check_clip_status(clip_id):
    """
    Endpoint pour vérifier le statut de génération d'un clip.
    """
    try:
        status = get_clip_status(clip_id)
        
        if not status:
            return jsonify({
                'status': 'error',
                'message': 'Clip not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'clip_status': status
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
