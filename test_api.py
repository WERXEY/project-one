#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour l'API du générateur de clips "Best Of".
Ce script permet de tester les différentes fonctionnalités de l'API.
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000/api"
TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Vidéo de test (Rick Astley - Never Gonna Give You Up)

def test_health_check():
    """
    Teste l'endpoint de vérification de santé de l'API.
    """
    print("\n=== Test de l'endpoint /health ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Statut: {response.status_code}")
        print(f"Réponse: {response.json()}")
        
        if response.status_code == 200 and response.json().get('status') == 'success':
            print("✅ Test réussi: L'API est en ligne")
            return True
        else:
            print("❌ Test échoué: L'API n'est pas en ligne")
            return False
    
    except Exception as e:
        print(f"❌ Test échoué: {str(e)}")
        return False

def test_create_short_clip():
    """
    Teste la création d'un clip court.
    """
    print("\n=== Test de création d'un clip court ===")
    
    try:
        payload = {
            "url": TEST_YOUTUBE_URL,
            "mode": "short",
            "transitions": True
        }
        
        response = requests.post(f"{API_BASE_URL}/clips", json=payload)
        print(f"Statut: {response.status_code}")
        print(f"Réponse: {response.json()}")
        
        if response.status_code == 202 and response.json().get('clip_id'):
            clip_id = response.json().get('clip_id')
            print(f"✅ Test réussi: Clip court en cours de génération (ID: {clip_id})")
            return clip_id
        else:
            print("❌ Test échoué: Impossible de créer un clip court")
            return None
    
    except Exception as e:
        print(f"❌ Test échoué: {str(e)}")
        return None

def test_create_long_clip():
    """
    Teste la création d'un clip long.
    """
    print("\n=== Test de création d'un clip long ===")
    
    try:
        payload = {
            "url": TEST_YOUTUBE_URL,
            "mode": "long",
            "transitions": True
        }
        
        response = requests.post(f"{API_BASE_URL}/clips", json=payload)
        print(f"Statut: {response.status_code}")
        print(f"Réponse: {response.json()}")
        
        if response.status_code == 202 and response.json().get('clip_id'):
            clip_id = response.json().get('clip_id')
            print(f"✅ Test réussi: Clip long en cours de génération (ID: {clip_id})")
            return clip_id
        else:
            print("❌ Test échoué: Impossible de créer un clip long")
            return None
    
    except Exception as e:
        print(f"❌ Test échoué: {str(e)}")
        return None

def test_invalid_url():
    """
    Teste la validation des URLs invalides.
    """
    print("\n=== Test de validation des URLs invalides ===")
    
    try:
        payload = {
            "url": "https://invalid-url.com/video",
            "mode": "short"
        }
        
        response = requests.post(f"{API_BASE_URL}/clips", json=payload)
        print(f"Statut: {response.status_code}")
        print(f"Réponse: {response.json()}")
        
        if response.status_code == 400:
            print("✅ Test réussi: L'API a correctement rejeté l'URL invalide")
            return True
        else:
            print("❌ Test échoué: L'API n'a pas correctement validé l'URL")
            return False
    
    except Exception as e:
        print(f"❌ Test échoué: {str(e)}")
        return False

def test_invalid_mode():
    """
    Teste la validation des modes invalides.
    """
    print("\n=== Test de validation des modes invalides ===")
    
    try:
        payload = {
            "url": TEST_YOUTUBE_URL,
            "mode": "invalid_mode"
        }
        
        response = requests.post(f"{API_BASE_URL}/clips", json=payload)
        print(f"Statut: {response.status_code}")
        print(f"Réponse: {response.json()}")
        
        if response.status_code == 400:
            print("✅ Test réussi: L'API a correctement rejeté le mode invalide")
            return True
        else:
            print("❌ Test échoué: L'API n'a pas correctement validé le mode")
            return False
    
    except Exception as e:
        print(f"❌ Test échoué: {str(e)}")
        return False

def test_get_clip_status(clip_id):
    """
    Teste la récupération du statut d'un clip.
    
    Args:
        clip_id: Identifiant du clip à vérifier
    """
    print(f"\n=== Test de récupération du statut du clip {clip_id} ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/clips/{clip_id}/status")
        print(f"Statut: {response.status_code}")
        print(f"Réponse: {response.json()}")
        
        if response.status_code == 200 and response.json().get('clip_status'):
            print(f"✅ Test réussi: Statut du clip récupéré")
            return response.json().get('clip_status')
        else:
            print("❌ Test échoué: Impossible de récupérer le statut du clip")
            return None
    
    except Exception as e:
        print(f"❌ Test échoué: {str(e)}")
        return None

def test_get_clip_info(clip_id):
    """
    Teste la récupération des informations d'un clip.
    
    Args:
        clip_id: Identifiant du clip à récupérer
    """
    print(f"\n=== Test de récupération des informations du clip {clip_id} ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/clips/{clip_id}")
        print(f"Statut: {response.status_code}")
        print(f"Réponse: {response.json()}")
        
        if response.status_code == 200 and response.json().get('clip'):
            print(f"✅ Test réussi: Informations du clip récupérées")
            return response.json().get('clip')
        else:
            print("❌ Test échoué: Impossible de récupérer les informations du clip")
            return None
    
    except Exception as e:
        print(f"❌ Test échoué: {str(e)}")
        return None

def test_invalid_clip_id():
    """
    Teste la récupération d'un clip avec un identifiant invalide.
    """
    print("\n=== Test de récupération d'un clip avec un identifiant invalide ===")
    
    try:
        invalid_id = "invalid_clip_id"
        response = requests.get(f"{API_BASE_URL}/clips/{invalid_id}")
        print(f"Statut: {response.status_code}")
        print(f"Réponse: {response.json()}")
        
        if response.status_code == 404:
            print("✅ Test réussi: L'API a correctement rejeté l'identifiant invalide")
            return True
        else:
            print("❌ Test échoué: L'API n'a pas correctement validé l'identifiant")
            return False
    
    except Exception as e:
        print(f"❌ Test échoué: {str(e)}")
        return False

def wait_for_clip_completion(clip_id, timeout=300, check_interval=10):
    """
    Attend la fin de la génération d'un clip.
    
    Args:
        clip_id: Identifiant du clip à attendre
        timeout: Temps maximum d'attente en secondes
        check_interval: Intervalle de vérification en secondes
        
    Returns:
        Le statut final du clip ou None en cas de timeout
    """
    print(f"\n=== Attente de la fin de génération du clip {clip_id} ===")
    
    start_time = time.time()
    elapsed_time = 0
    
    while elapsed_time < timeout:
        status = test_get_clip_status(clip_id)
        
        if not status:
            return None
        
        if status.get('status') in ['completed', 'failed']:
            print(f"Génération terminée avec le statut: {status.get('status')}")
            return status
        
        print(f"Statut actuel: {status.get('status')} - Attente de {check_interval} secondes...")
        time.sleep(check_interval)
        
        elapsed_time = time.time() - start_time
        print(f"Temps écoulé: {int(elapsed_time)} secondes")
    
    print(f"❌ Timeout après {timeout} secondes")
    return None

def run_all_tests():
    """
    Exécute tous les tests de l'API.
    """
    print("=== Début des tests de l'API du générateur de clips ===")
    print(f"URL de base de l'API: {API_BASE_URL}")
    print(f"Date et heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test de santé
    if not test_health_check():
        print("\n❌ L'API n'est pas accessible. Arrêt des tests.")
        return
    
    # Tests de validation
    test_invalid_url()
    test_invalid_mode()
    test_invalid_clip_id()
    
    # Test de création de clip court
    short_clip_id = test_create_short_clip()
    if short_clip_id:
        # Attente de la fin de génération (max 5 minutes)
        final_status = wait_for_clip_completion(short_clip_id, timeout=300)
        if final_status and final_status.get('status') == 'completed':
            test_get_clip_info(short_clip_id)
    
    # Test de création de clip long
    long_clip_id = test_create_long_clip()
    if long_clip_id:
        # Vérification du statut initial
        test_get_clip_status(long_clip_id)
        # Note: On ne va pas attendre la fin de la génération du clip long
        # car cela pourrait prendre trop de temps
    
    print("\n=== Fin des tests de l'API du générateur de clips ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de test pour l'API du générateur de clips")
    parser.add_argument("--url", default=API_BASE_URL, help="URL de base de l'API")
    parser.add_argument("--youtube", default=TEST_YOUTUBE_URL, help="URL YouTube de test")
    
    args = parser.parse_args()
    
    API_BASE_URL = args.url
    TEST_YOUTUBE_URL = args.youtube
    
    run_all_tests()
