import sqlite3
from config import config

con = sqlite3.connect(config['databaseFile']) # on charge la base de données SQLite
cur = con.cursor() # on définit son curseur