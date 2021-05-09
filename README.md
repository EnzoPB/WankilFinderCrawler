# WankilFinder Crawler
Archive les données des vidéos d'une chaine via l'[API Youtube data V3](https://developers.google.com/youtube/v3) avec ID, titre, description, date de publication, top commentaires, sous-titres manuels & automatiques, pour [Wankil Finder](https://www.reddit.com/r/wankil/comments/n68uvb/wankilfinder_projet).

## But
Le but est d'être utilisé dans le [Wankil Finder](https://www.reddit.com/r/wankil/comments/n68uvb/wankilfinder_projet), les données archivés serviront de données de recherche, permettant de rechercher une vidéo de Wankil Studio (le crawler est toutefois configurable pour n'importe quelle chaîne) à partir de mots-clés.

## Utilisation
Nécéssite les modules [youtube_transcript_api](https://pypi.org/project/youtube-transcript-api), [requests](https://pypi.org/project/requests):
`pip3 install youtube-transcript-api requests`

Il faut renommer `config.sample.py` en `config.py`, en renseignant `APIKey` avec la [clé API](https://developers.google.com/youtube/v3/getting-started#before-you-start)  et `playlistId` avec l'ID de la playlist dans laquelle prendre les vidéos. Le `databaseFile` est le fichier SQLite, par défaut videos.db (le fichier videos.db est juste la base de données vide, uniquement avec la structure).

Puis il suffit de lancer le script:
`python3 crawler.py`
Testé avec Python 3.8.6, mais devrait marcher avec toute versions > 3.
Le script prend entre 0.5s et 1.5s par vidéos (actuellement, avec 845 vidéos c'est ~1000 secondes)

## License
License MIT (voir le fichier [LICENSE](https://github.com/EnzoPB/WankilFinderCrawler/blob/master/LICENSE))