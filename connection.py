import mysql.connector

# Connexion à la base de données
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Bossmed@2008",
    database="mb_design"
)

# Créer un curseur pour exécuter les commandes SQL
mycursor = mydb.cursor()