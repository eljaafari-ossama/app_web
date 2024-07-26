import os
import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
from twilio.rest import Client
from PIL import Image  # Pour afficher des images (logo)
from io import BytesIO
from fpdf import FPDF  # Pour exporter en PDF
import tempfile  # Pour créer des fichiers temporaires

# Paramètres pour Twilio (notifications SMS)
TWILIO_ACCOUNT_SID = 'ACfc88fe81dac5be54b784c80772830cca'
TWILIO_AUTH_TOKEN = '6292e1aa005dc7ef9484bd25db7c7b00'
TWILIO_PHONE_NUMBER = '+12073465637'
YOUR_PHONE_NUMBER = '+212696939473'

# Fonction pour envoyer des alertes par SMS
def send_sms_alert(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=YOUR_PHONE_NUMBER
    )
    st.success("Alerte envoyée par SMS.")

# Fonction pour se connecter à la base de données MySQL
def get_connection():
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '1234'),
        'database': os.getenv('DB_NAME', 'report_database')
    }
    conn = mysql.connector.connect(**db_config)
    return conn

# Fonction pour lire les données de la table report_table
def read_data(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Fonction pour lire les données en temps réel
def read_latest_data():
    query = "SELECT * FROM report_table ORDER BY date_temps DESC LIMIT 1"
    return read_data(query)

# Fonction pour calculer les statistiques
def calculate_statistics(df):
    return df.describe()

# Fonction pour visualiser les données
def plot_data(df):
    if 'date_temps' in df.columns and 'Pressure' in df.columns and 'GasLevel' in df.columns:
        df['date_temps'] = pd.to_datetime(df['date_temps'])
        st.line_chart(df[['date_temps', 'Pressure', 'GasLevel']].set_index('date_temps'))
    else:
        st.error("Colonnes nécessaires non trouvées.")

# Fonction pour exporter les données en PDF
def export_to_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Ajouter le titre
    pdf.cell(200, 10, txt="Données Exportées", ln=True, align='C')
    
    # Ajouter les données
    for i, row in df.iterrows():
        pdf.cell(200, 10, txt=str(row.values), ln=True, align='L')
    
    # Créer un fichier temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        pdf_output_path = temp_file.name
        pdf.output(pdf_output_path)
    
    # Lire le contenu du fichier temporaire
    with open(pdf_output_path, 'rb') as f:
        pdf_data = f.read()
    
    # Supprimer le fichier temporaire
    os.remove(pdf_output_path)
    
    return pdf_data

# Configuration de la sidebar pour la navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Aller à", ["Accueil", "Données en temps réel", "Historique des données", "FAQ", "À propos"])

# Page d'accueil
if page == "Accueil":
    st.title("Bienvenue sur SOMAS Data Monitor")
    
    # Afficher le logo de l'entreprise
    logo = Image.open('téléchargement.jpg')  # Remplacez par le chemin vers votre logo
    st.image(logo, caption='', use_column_width=True)
    
    st.write("Pour toute question ou support, veuillez nous contacter: eljaafarioussama9@gmail.com")

# Page de données en temps réel
elif page == "Données en temps réel":
    st.title("Données en temps réel")
    st.write("Voici les dernières données enregistrées :")

    # Ajouter un bouton pour actualiser les données
    if st.button('Actualiser maintenant'):
        st.session_state.last_refresh = datetime.now()
    
    # Affichage des données les plus récentes
    last_refresh = st.session_state.get('last_refresh', datetime.now() - timedelta(seconds=10))
    if (datetime.now() - last_refresh).total_seconds() > 10:
        st.session_state.last_refresh = datetime.now()

    latest_data = read_latest_data()

    if not latest_data.empty:
        st.write(latest_data)
        data = latest_data.iloc[0]

        # Vérifications d'alerte et envoi de SMS
        if data['Pressure'] > 80:
            send_sms_alert("Alerte de Pression : La pression dépasse 80%!")
        if data['Alarm1']:
            send_sms_alert("Alerte de Haute Pression : L'alarme de haute pression est activée!")
        if data['Alarm2']:
            send_sms_alert("Alerte de Fuite : L'alarme de fuite est activée!")
        if data['LeakDetected']:
            send_sms_alert("Alerte de Fuite Détectée : Une fuite a été détectée!")
        if data['arret_urgence']:
            send_sms_alert("Alerte d'Arrêt d'Urgence : L'arrêt d'urgence est activé!")
    else:
        st.error("Aucune donnée disponible.")

    # Affichage des données automatiquement toutes les 10 secondes
    if (datetime.now() - last_refresh).total_seconds() > 10:
        st.session_state.last_refresh = datetime.now()

# Page d'historique des données
elif page == "Historique des données":
    st.title("Historique des données")
    st.write("Consultez l'historique complet des données de stockage de gaz butane. Vous pouvez choisir de voir toutes les données ou de sélectionner une date spécifique pour obtenir des informations détaillées.")

    # Choisir une date spécifique ou toutes les données
    date_option = st.selectbox("Sélectionnez une option", ["Toutes les données", "Sélectionner une date"])
    
    if date_option == "Toutes les données":
        data = read_data("SELECT * FROM report_table")
        st.write(data)
        
        # Calcul des statistiques
        st.subheader("Statistiques des Données")
        if not data.empty:
            st.write(calculate_statistics(data))
        
        # Visualisation des données
        st.subheader("Visualisation des Données")
        if not data.empty:
            plot_data(data)
        
        # Options de téléchargement
        st.subheader("Téléchargement des Données")
        
        # Téléchargement CSV
        csv = data.to_csv(index=False)
        st.download_button(label="Télécharger les données en CSV", data=csv, file_name='historique_donnees.csv', mime='text/csv')
        
        # Téléchargement Excel
        excel = BytesIO()
        data.to_excel(excel, index=False)
        excel.seek(0)
        st.download_button(label="Télécharger les données en Excel", data=excel.getvalue(), file_name='historique_donnees.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Téléchargement JSON
        json_data = data.to_json(orient='records')
        st.download_button(label="Télécharger les données en JSON", data=json_data, file_name='historique_donnees.json', mime='application/json')
        
        # Téléchargement PDF
        pdf_data = export_to_pdf(data)
        st.download_button(label="Télécharger les données en PDF", data=pdf_data, file_name='historique_donnees.pdf', mime='application/pdf')
    
    elif date_option == "Sélectionner une date":
        selected_date = st.date_input("Choisir une date", datetime.now())
        start_date = selected_date.strftime('%Y-%m-%d 00:00:00')
        end_date = (selected_date + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
        
        query = f"SELECT * FROM report_table WHERE date_temps BETWEEN '{start_date}' AND '{end_date}'"
        data = read_data(query)
        st.write(data)
        
        # Calcul des statistiques
        st.subheader("Statistiques des Données")
        if not data.empty:
            st.write(calculate_statistics(data))
        
        # Visualisation des données
        st.subheader("Visualisation des Données")
        if not data.empty:
            plot_data(data)
        
        # Options de téléchargement
        st.subheader("Téléchargement des Données")
        
        # Téléchargement CSV
        csv = data.to_csv(index=False)
        st.download_button(label="Télécharger les données en CSV", data=csv, file_name=f'donnees_{selected_date}.csv', mime='text/csv')
        
        # Téléchargement Excel
        excel = BytesIO()
        data.to_excel(excel, index=False)
        excel.seek(0)
        st.download_button(label="Télécharger les données en Excel", data=excel.getvalue(), file_name=f'donnees_{selected_date}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Téléchargement JSON
        json_data = data.to_json(orient='records')
        st.download_button(label="Télécharger les données en JSON", data=json_data, file_name=f'donnees_{selected_date}.json', mime='application/json')
        
        # Téléchargement PDF
        pdf_data = export_to_pdf(data)
        st.download_button(label="Télécharger les données en PDF", data=pdf_data, file_name=f'donnees_{selected_date}.pdf', mime='application/pdf')

# Page FAQ
elif page == "FAQ":
    st.title("FAQ")
    st.write("### Comment utiliser l'application")
    st.write("Voici les questions les plus fréquentes et leurs réponses.")

# Page "À propos"
elif page == "À propos":
    st.title("À propos de l'application")
    
    st.write("### SOMAS Data Monitor")
    st.write("SOMAS Data Monitor est une application développée pour surveiller les données en temps réel des installations de stockage de gaz butane. Elle offre des fonctionnalités pour consulter les données actuelles, l'historique des données, et recevoir des alertes en cas d'anomalie.")
    
    st.write("### Développé par")
    st.write("**Oussama El Jaaafari**")
    st.write("Étudiant en première année de master à l'ENSET de Mohammedia.")

    st.write("### À propos de l'entreprise")
    st.write("**SOMAS** est une entreprise spécialisée dans le stockage et la gestion du gaz butane. Elle se consacre à fournir des solutions fiables et sécurisées pour le stockage de ce gaz essentiel.")
