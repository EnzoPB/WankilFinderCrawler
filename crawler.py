from youtube_transcript_api import YouTubeTranscriptApi, _errors as YouTubeTranscriptApiErrors
import mysql.connector
from datetime import datetime
import json
import re

from youtubeAPI import youtubeAPI # on importe la fonction youtubeAPI, qui sert juste à formatter des requêtes à l'API youtube
from config import config

db = mysql.connector.connect(**config['database']) # connexion à la bdd MySQL
cur = db.cursor()

nextPageToken = '' # token retourné par l'API pour accéder à la page de la playlist suivante
run = True
if __name__ == '__main__':
    while run:
        # on récupère toute les vidéos de la chaine depuis l'API (via la playlist 'uploads')
        playlist = youtubeAPI('playlistItems', {
            'part': 'snippet',
            'pageToken': nextPageToken,
            'maxResults': 50, # on veux 50 vidéos (le max. par requètes)
            'playlistId': config['playlistId'] # ID de la playlist "uploads"
        })
        if 'nextPageToken' in playlist:
            nextPageToken = playlist['nextPageToken']
        else:
            run = False

        videos = playlist['items'] # 'items' correspond à la liste des vidéos

        for video in videos:
            video = video['snippet']
            videoId = video['resourceId']['videoId']

            print(f'Video #{video["position"]}: {videoId} {video["title"]}')

            # on regarde si la video existe deja dans la bdd
            cur.execute('SELECT COUNT(*) FROM wkl_videos WHERE id=%s', (videoId,))
            if cur.fetchall()[0][0] != 0:
                print('Vidéo déjà éxistante')
                continue

            timestamp = datetime.strptime(video['publishedAt'], '%Y-%m-%dT%H:%M:%SZ') # on transforme la date ISO8601 en timestamp UNIX
            
            # on extrait le jeu depuis le titre de la vidéo
            # l'idéal serait de récupérer le jeu détécté par Youtube, mais on ne peut pas y accéder depuis l'API 
            reg = re.findall('\((.*?)\)', video['title'])
            game = ''
            if len(reg) != 0:
                game = reg[0]

            # on regarde si le jeu est déjà dans la BDD
            cur.execute('SELECT COUNT(*) FROM wkl_games WHERE name=%s', (game,))
            if cur.fetchall()[0][0] == 0: # il n'existe pas dans la bdd, on le créer
                cur.execute('INSERT INTO wkl_games(name) VALUES(%s)', (game,))
                db.commit()

            # on créér une nouvelle ligne dans la bdd
            cur.execute('INSERT INTO wkl_videos(id, title, description, timestamp, game) VALUES(%s, %s, %s, %s, %s)',
                (videoId, video['title'], video['description'], timestamp, game))
            db.commit()

            # on récupère les 50 premiers commentaires
            comments = youtubeAPI('commentThreads', {
                'part': 'snippet',
                'textFormat': 'plainText', # on veux les commentaires en texte simple
                'maxResults': 50, # on veut 50 commentaires
                'order': 'relevance', # on trie par 'relevance' (ordre par defaut)
                'videoId': videoId # ID de la vidéo
            })['items'] # 'items' correspond à la liste des commentaires
    
            for comment in comments:
                comment = comment['snippet']['topLevelComment']['snippet']
                # on ajoute le commentaire dans la base de donnée (auteur + texte)
                cur.execute('INSERT INTO wkl_comments(video_id, author, text) VALUES(%s, %s, %s)',
                    (videoId, comment['authorDisplayName'], comment['textDisplay']))

            try:
                # on récupère les sous-titres français de la vidéo (automatiques et manuels) voir https://pypi.org/project/youtube-transcript-api
                transcripts = YouTubeTranscriptApi.list_transcripts(videoId) # on récupère la liste des sous-titres pour la vidéos
            except YouTubeTranscriptApiErrors.TranscriptsDisabled: # les sous-titres sont désactivés pour cette vidéo
                pass # on ignore l'erreur, rien n'est ajouté dans l'array

            try:
                autoCaptions = transcripts.find_generated_transcript(['fr']).fetch() # on récupère les sous-titres automatiques en français
                for caption in autoCaptions:
                    # on ajoute le timestamp et texte du sous-titre à la base de données
                    cur.execute('INSERT INTO wkl_captions(video_id, timestamp, text, type) VALUES(%s, %s, %s, %s)',
                        (videoId, int(caption['start']), caption['text'], 1)) # type 1 = sous-titres auto
            except YouTubeTranscriptApiErrors.NoTranscriptFound: # les sous-titres sont désactivés / indisponibles
                pass # on ignore l'erreur, rien n'est ajouté dans l'array

            manualCaptionsList = [] # liste contenant les sous-titres manuels
            try:
                manualCaptions = transcripts.find_manually_created_transcript(['fr']).fetch() # on récupère les sous-titres manuels en français
                for caption in manualCaptions:
                    # on ajoute le timestamp et texte du sous-titre à la base de données
                    cur.execute('INSERT INTO wkl_captions(video_id, timestamp, text, type) VALUES(%s, %s, %s, %s)',
                        (videoId, int(caption['start']), caption['text'], 0)) # type 0 = sous-titres manuels
            except YouTubeTranscriptApiErrors.NoTranscriptFound: # les sous-titres sont indisponibles
                pass # on ignore l'erreur, rien n'est ajouté dans l'array

            db.commit()

db.close()