from flask import Flask, render_template, send_from_directory, jsonify, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from connection import mydb, mycursor  # Assurez-vous que connection.py est correctement configuré
import mysql.connector
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Clé secrète pour les sessions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        full_name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not full_name or not email or not message:
            return jsonify({'message': 'All fields are required'}), 400

        try:
            sql = """
                INSERT INTO contact_messages (full_name, email, message)
                VALUES (%s, %s, %s)
            """
            data = (full_name, email, message)
            mycursor.execute(sql, data)
            mydb.commit()
            return jsonify({'message': 'Message sent successfully! Thank you for contacting us.'}), 200
        except mysql.connector.Error as err:
            mydb.rollback()
            print(f"Error inserting contact message: {err}")
            return jsonify({'message': 'Error sending message. Please try again later.'}), 500

    return render_template('contact.html')

@app.route('/contact-success')
def contact_success():
    return "Message sent successfully! Thank you for contacting us."

@app.route('/design')
def design():
    return render_template('design.html')

@app.route('/remove_from_basket/<int:design_id>', methods=['POST'])
def remove_from_basket(design_id):
    if 'logged_in' in session:
        username = session['username']
        try:
            # Supprimer le design du panier de l'utilisateur
            sql = "DELETE FROM basket WHERE username = %s AND design_id = %s"
            data = (username, design_id)
            mycursor.execute(sql, data)
            mydb.commit()
            
            return redirect(url_for('basket'))
        except mysql.connector.Error as err:
            mydb.rollback()
            print(f"Erreur lors de la suppression du design du panier : {err}")
            return "Erreur lors de la suppression du design.", 500
    else:
        return redirect(url_for('login'))


@app.route('/basket')
def basket():
    if 'logged_in' in session:
        username = session['username']
        try:
            # Requête pour récupérer les designs et leur prix dans le panier de l'utilisateur
            mycursor.execute("""
                SELECT d.image_url, d.price, b.design_id
                FROM basket b
                JOIN designs d ON b.design_id = d.id
                WHERE b.username = %s
            """, (username,))
            basket_items = mycursor.fetchall()

            # Vérifiez les données récupérées
            print(basket_items)

            # Calculer la somme totale des achats
            total_price = sum(item[1] for item in basket_items)

            # Préparer les données pour le template
            basket_items = [{'image_url': item[0], 'price': item[1], 'design_id': item[2]} for item in basket_items]
            
            # Préparer le message pour WhatsApp
            order_details = 'Order Details:\n' + '\n'.join([f'Design ID: {item["design_id"]}, Price: ${item["price"]}' for item in basket_items])
            order_details += f'\n\nTotal Price: ${total_price:.2f}'
            encoded_message = urlencode({'text': order_details})

            return render_template('basket.html', basket_items=basket_items, encoded_message=encoded_message, total_price=total_price)
        except mysql.connector.Error as err:
            print(f"Erreur lors de la récupération des designs : {err}")
            return "Erreur lors de la récupération des designs.", 500
    else:
        return redirect(url_for('login'))


@app.route('/add-to-basket', methods=['POST'])
def add_to_basket():
    if 'logged_in' not in session:
        return jsonify({'message': 'You must be logged in to add items to the basket.'}), 403
    
    design_id = request.form.get('design_id')
    username = session.get('username')

    if not design_id:
        return jsonify({'message': 'Design ID is required.'}), 400

    try:
        sql = "INSERT INTO basket (username, design_id) VALUES (%s, %s)"
        data = (username, design_id)
        mycursor.execute(sql, data)
        mydb.commit()
        return jsonify({'message': 'Design added to basket successfully!'}), 200
    except mysql.connector.Error as err:
        mydb.rollback()
        print(f"Error adding to basket: {err}")
        return jsonify({'message': 'Error adding to basket. Please try again later.'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            # Trouver l'utilisateur dans la base de données
            mycursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            result = mycursor.fetchone()

            if result:
                stored_password = result[0]
                if check_password_hash(stored_password, password):
                    # Connexion réussie
                    session['logged_in'] = True
                    session['username'] = username
                    return redirect(url_for('index'))
                else:
                    # Échec de la connexion
                    return "Nom d'utilisateur ou mot de passe invalide.", 401
            else:
                return "Nom d'utilisateur ou mot de passe invalide.", 401
        except mysql.connector.Error as err:
            print(f"Erreur lors de la connexion : {err}")
            return "Erreur lors de la connexion.", 500

    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'logged_in' in session:
        username = session['username']
        try:
            # Trouver l'utilisateur dans la base de données
            mycursor.execute("SELECT full_name, username, email, phone_number FROM users WHERE username = %s", (username,))
            result = mycursor.fetchone()

            if result:
                full_name, username, email, phone_number = result
                user = {
                    'full_name': full_name,
                    'username': username,
                    'email': email,
                    'phone_number': phone_number
                }
                return render_template('profile.html', user=user)
            else:
                return "Utilisateur non trouvé.", 404
        except mysql.connector.Error as err:
            print(f"Erreur lors de la récupération des informations de l'utilisateur : {err}")
            return "Erreur lors de la récupération des informations.", 500
    else:
        return redirect(url_for('login'))

@app.route('/update-profile', methods=['GET', 'POST'])
def update_profile():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        user = session.get('username')

        try:
            sql = """
                UPDATE users
                SET full_name = %s, username = %s, email = %s, phone_number = %s
                WHERE username = %s
            """
            data = (full_name, username, email, phone_number, user)
            mycursor.execute(sql, data)
            mydb.commit()

            # Mise à jour des informations de session
            session['username'] = username

            return redirect(url_for('profile'))
        except mysql.connector.Error as err:
            mydb.rollback()  # Annuler les modifications en cas d'erreur
            print(f"Erreur lors de la mise à jour du profil : {err}")
            return "Erreur lors de la mise à jour.", 500

    # Récupérer les informations actuelles de l'utilisateur
    user = session.get('username')
    mycursor.execute("SELECT full_name, username, email, phone_number FROM users WHERE username = %s", (user,))
    result = mycursor.fetchone()

    if not result:
        return redirect(url_for('login'))

    return render_template('update_profile.html', user=result)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone_number = request.form.get('phone')
        country_code = request.form.get('country_code')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return "Les mots de passe ne correspondent pas.", 400

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            # Insérer l'utilisateur dans la base de données
            sql = """
                INSERT INTO users (full_name, username, email, phone_number, password)
                VALUES (%s, %s, %s, %s, %s)
            """
            data = (full_name, username, email, phone_number, hashed_password)
            mycursor.execute(sql, data)
            mydb.commit()
            return redirect(url_for('login'))  # Rediriger vers la page de connexion
        except mysql.connector.Error as err:
            mydb.rollback()  # Annuler les modifications en cas d'erreur
            print(f"Erreur lors de l'inscription de l'utilisateur : {err}")
            return "Erreur lors de l'inscription.", 500

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/Design/<path:filename>')
def serve_design(filename):
    return send_from_directory('Design', filename)

@app.route('/<path:filename>')
def serve_logo(filename):
    return send_from_directory('', filename)

@app.route('/list-designs')
def list_designs():
    try:
        mycursor.execute("SELECT id, image_url, price FROM designs")
        results = mycursor.fetchall()
        designs = [{'id': row[0], 'image_url': row[1], 'price': row[2]} for row in results]
        return jsonify(designs)
    except mysql.connector.Error as err:
        print(f"Error retrieving designs: {err}")
        return jsonify({'message': 'Error retrieving designs'}), 500

if __name__ == "__main__":
    app.run(debug=True)
