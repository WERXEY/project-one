document.addEventListener('DOMContentLoaded', function() {
    // Gestion du formulaire de génération de clip
    const clipForm = document.getElementById('clip-form');
    if (clipForm) {
        clipForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const youtubeUrl = document.getElementById('youtube-url').value;
            const clipMode = document.querySelector('input[name="clip-mode"]:checked').value;
            const transitions = document.getElementById('transitions').checked;
            
            // Afficher l'indicateur de chargement
            document.getElementById('loading-indicator').classList.remove('d-none');
            document.getElementById('form-submit-btn').disabled = true;
            
            // Appel à l'API pour générer le clip
            fetch('/api/clips', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: youtubeUrl,
                    mode: clipMode,
                    transitions: transitions
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Rediriger vers la page de statut du clip
                    window.location.href = `/clip/${data.clip_id}`;
                } else {
                    // Afficher l'erreur
                    showError(data.message);
                }
            })
            .catch(error => {
                showError('Une erreur est survenue lors de la communication avec le serveur.');
                console.error('Error:', error);
            })
            .finally(() => {
                // Masquer l'indicateur de chargement
                document.getElementById('loading-indicator').classList.add('d-none');
                document.getElementById('form-submit-btn').disabled = false;
            });
        });
    }
    
    // Fonction pour afficher les erreurs
    function showError(message) {
        const errorAlert = document.getElementById('error-alert');
        if (errorAlert) {
            errorAlert.textContent = message;
            errorAlert.classList.remove('d-none');
            
            // Masquer l'alerte après 5 secondes
            setTimeout(() => {
                errorAlert.classList.add('d-none');
            }, 5000);
        }
    }
    
    // Gestion de la page de statut du clip
    const clipStatusContainer = document.getElementById('clip-status-container');
    if (clipStatusContainer) {
        const clipId = clipStatusContainer.dataset.clipId;
        
        // Fonction pour mettre à jour le statut du clip
        function updateClipStatus() {
            fetch(`/api/clips/${clipId}/status`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        const clipStatus = data.clip_status;
                        
                        // Mettre à jour l'affichage du statut
                        document.getElementById('clip-status').textContent = clipStatus.status;
                        
                        // Si le clip est terminé ou en erreur, arrêter les mises à jour
                        if (clipStatus.status === 'completed') {
                            clearInterval(statusInterval);
                            document.getElementById('clip-ready-container').classList.remove('d-none');
                        } else if (clipStatus.status === 'error') {
                            clearInterval(statusInterval);
                            document.getElementById('clip-error-container').classList.remove('d-none');
                            document.getElementById('clip-error-message').textContent = clipStatus.error;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        }
        
        // Mettre à jour le statut toutes les 3 secondes
        const statusInterval = setInterval(updateClipStatus, 3000);
        
        // Mettre à jour le statut immédiatement
        updateClipStatus();
    }
});
