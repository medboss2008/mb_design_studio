from connection import mydb, mycursor
import mysql.connector
from werkzeug.security import generate_password_hash

# Fonction pour insérer un utilisateur dans la base de données
def insert_user(full_name, username, email, phone_number, password):
    sql = """
        INSERT INTO users (full_name, username, email, phone_number, password)
        VALUES (%s, %s, %s, %s, %s)
    """
    
    data = (full_name, username, email, phone_number, password)

    try:
        # Exécuter la requête SQL
        mycursor.execute(sql, data)
        # Valider les modifications
        mydb.commit()
        print("Utilisateur inséré avec succès.")
    except mysql.connector.Error as err:
        # Annuler les modifications en cas d'erreur
        mydb.rollback()
        print(f"Erreur lors de l'insertion de l'utilisateur : {err}")

# Exemple d'appel de la fonction avec mot de passe haché
def main():
    full_name = "John Doe"
    username = "johndoe"
    email = "john@example.com"
    phone_number = "123456789"
    password = "plain_password"  # Le mot de passe en clair
    
    # Hacher le mot de passe
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    # Appeler la fonction d'insertion avec le mot de passe haché
    insert_user(full_name, username, email, phone_number, hashed_password)

if __name__ == "__main__":
    main()
