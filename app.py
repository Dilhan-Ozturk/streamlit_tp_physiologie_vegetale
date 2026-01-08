import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Travaux pratiques - physiologie végétale", layout="wide")

st.title("Collecte de données : Conductance & PAR")

# Connexion au Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des données (ttl=0 pour forcer la mise à jour à chaque refresh)
data = conn.read(ttl=0)

# --- SECTION 1 : AFFICHAGE ---
st.subheader("Données enregistrées")
st.dataframe(data, use_container_width=True)

# --- SECTION 2 : FORMULAIRE D'AJOUT ---
st.divider()
st.subheader("Ajouter une nouvelle mesure")

with st.form("form_saisie", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        # Date et Heure avec widgets dédiés (formatage automatique)
        date_val = st.date_input("Date")
        heure_val = st.time_input("Heure (hh:mm)")
        
        rang_feuille = st.number_input("Rang feuille (#)", min_value=1, step=1)
        etat_feuille = st.selectbox("Etat feuille", ["Bien développée", "Jeune", "Vielle"])
        
    with col2:
        position = st.selectbox("Position sur le limbre", ["Base", "Milieu", "Pointe"])
        face = st.selectbox("Face", ["Abaxiale", "Adaxiale"])
        
        # Champs numériques avec précision décimale
        conductance = st.number_input("Conductance stomatique (mmol/m².s)", format="%.1f", step=0.1)
        par = st.number_input("PAR (µmol/m².s)", format="%.1f", step=0.1)

    submit = st.form_submit_button("Enregistrer la mesure")

    if submit:
        # 1. Préparation de la nouvelle ligne au format exact des colonnes
        new_entry = {
            "Date (jj/mm/yyyy)": date_val.strftime("%d/%m/%Y"),
            "Heure (hh:mm)": heure_val.strftime("%H:%M"),
            "Rang feuille (#)": int(rang_feuille),
            "Etat feuille": etat_feuille,
            "Position sur le limbre (Base-milieu-pointe)": position,
            "Face (Abaxiale-Adaxiale)": face,
            "Conductance stomatique (mmol/m².s)": conductance,
            "PAR (µmol/m².s)": par
        }
        
        # 2. Ajout à la base existante
        new_row_df = pd.DataFrame([new_entry])
        updated_df = pd.concat([data, new_row_df], ignore_index=True)
        
        # 3. Envoi vers Google Sheets
        try:
            conn.update(data=updated_df)
            st.success("Données ajoutées avec succès !")
            st.rerun() # Rafraîchit l'affichage
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement : {e}")

# --- SECTION 3 : EXPORT ---
st.divider()
csv = data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Télécharger le fichier complet (CSV)",
    data=csv,
    file_name=f"mesures_physio_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
)
