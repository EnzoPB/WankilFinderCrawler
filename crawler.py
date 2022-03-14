from youtube_transcript_api import YouTubeTranscriptApi, _errors as YouTubeTranscriptApiErrors
from datetime import datetime
import json

from database import con, cur # on importe la connexion et le curseur de la base de donnée
from youtubeAPI import youtubeAPI # on importe la fonction youtubeAPI, qui sert juste à formatter des requêtes à l'API youtube
from config import config

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

            timestamp = datetime.strptime(video['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').timestamp() # on transforme la date ISO8601 en timestamp UNIX

            # on récupère les 50 premiers commentaires
            topComments = [] # liste contenant ces commenaires
            comments = youtubeAPI('commentThreads', {
                'part': 'snippet',
                'textFormat': 'plainText', # on veux les commentaires en texte simple
                'maxResults': 50, # on veut 50 commentaires
                'order': 'relevance', # on trie par 'relevance' (ordre par defaut)
                'videoId': videoId # ID de la vidéo
            })['items'] # 'items' correspond à la liste des commentaires

            for comment in comments:
                comment = comment['snippet']['topLevelComment']['snippet']
                topComments.append([
                    comment['authorDisplayName'],
                    comment['textDisplay']
                ]) # on ajoute le commentaire à la liste (uniquement l'auteur et le texte)

            try:
                # on récupère les sous-titres français de la vidéo (automatiques et manuels) voir https://pypi.org/project/youtube-transcript-api
                transcripts = YouTubeTranscriptApi.list_transcripts(videoId) # on récupère la liste des sous-titres pour la vidéos
            except YouTubeTranscriptApiErrors.TranscriptsDisabled: # les sous-titres sont désactivés pour cette vidéo
                pass # on ignore l'erreur, rien n'est ajouté dans l'array

            autoCaptionsList = [] # liste contenant les sous-titres automatiques
            try:
                autoCaptions = transcripts.find_generated_transcript(['fr']).fetch() # on récupère les sous-titres automatiques en français
                for caption in autoCaptions:
                    autoCaptionsList.append([
                        caption['start'],
                        caption['text']
                    ]) # on ajoute le timestamp et texte du sous-titre à la liste
            except YouTubeTranscriptApiErrors.NoTranscriptFound: # les sous-titres sont désactivés / indisponibles
                pass # on ignore l'erreur, rien n'est ajouté dans l'array

            manualCaptionsList = [] # liste contenant les sous-titres manuels
            try:
                manualCaptions = transcripts.find_manually_created_transcript(['fr']).fetch() # on récupère les sous-titres manuels en français
                for caption in manualCaptions:
                    manualCaptionsList.append([
                        caption['start'],
                        caption['text']
                    ]) # on ajoute le timestamp et texte du sous-titre à la liste
            except YouTubeTranscriptApiErrors.NoTranscriptFound: # les sous-titres sont indisponibles
                pass # on ignore l'erreur, rien n'est ajouté dans l'array

            # on convertit les sous titres et les commentaires en JSON
            manualCaptionsList = json.dumps(manualCaptionsList)
            autoCaptionsList = json.dumps(autoCaptionsList)
            topComments = json.dumps(topComments)

            # on créér une nouvelle ligne dans la bdd
            cur.execute('INSERT INTO videos(id, title, description, timestamp, topComments, autoCaptions, manualCaptions) VALUES(?, ?, ?, ?, ?, ?, ?)',
                (videoId, video['title'], video['description'], timestamp, topComments, autoCaptionsList, manualCaptionsList))
            con.commit()
con.close()