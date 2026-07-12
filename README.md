# Veille Globale Unifiée (Automatisée)

Ce dépôt contient les scripts d'automatisation de la Veille Globale (Actualités, IA, Météo & Vidéos YouTube) de Gregory.

## Structure
* `run_veille.py` : Script d'orchestration principal.
* `fetch_youtube_feed.py` : Collecte et tri des 10 meilleures vidéos YouTube.
* `subscriptions.json` : Liste des 108 chaînes YouTube suivies.
* `.github/workflows/veille_quotidienne.yml` : Workflow planifié pour s'exécuter 5 fois par jour (8h, 12h, 16h, 20h, 23h).

## Configuration
Le workflow GitHub Actions utilise les secrets suivants à configurer sur votre dépôt :
* `SMTP_PASSWORD` : Mot de passe de messagerie SFR pour l'envoi.
* `OPENROUTER_API_KEY` : Clé API OpenRouter pour la rédaction automatique par DeepSeek.
