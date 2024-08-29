import os
import mysql.connector

# Connexion à la base de données
mydb = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '3306'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', 'Bossmed@2008'),
    database=os.getenv('DB_NAME', 'mb_design')
)

# Créer un curseur pour exécuter les commandes SQL
mycursor = mydb.cursor()
