import streamlit as st
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Collecte des données - Travaux pratiques physiologie végétale", layout="wide")

# Connexion Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FONCTION : SAUVEGARDE ---
def save_data(spreadsheet_key, new_row_dict):
    try:
        # 1. Configuration des credentials à partir des secrets Streamlit
        sks = st.secrets["connections"]["gsheets"]
        
        credentials_dict = {
            "type": "service_account",
            "project_id": sks["project_id"],
            "private_key_id": sks["private_key_id"],
            "private_key": sks["private_key"],
            "client_email": sks["client_email"],
            "client_id": sks["client_id"],
            "auth_uri": sks["auth_uri"],
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": sks.get("client_x509_cert_url") # optionnel selon votre JSON
        }

        # 2. Authentification avec gspread
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 3. Ouverture du fichier et ajout de la ligne
        url = sks[spreadsheet_key]
        sheet = client.open_by_url(url).sheet1
        
        # Transformer le dictionnaire en liste de valeurs
        values = list(new_row_dict.values())
        
        # L'opération magique qui ne supprime rien : append_row
        sheet.append_row(values)
        
        st.toast("Données enregistrées !", icon="✅")
        
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")
        
# --- FONCTION : VISUALISATION ---
def visualiser_donnees(spreadsheet_key, label):
    try:
        url = st.secrets["connections"]["gsheets"][spreadsheet_key]
        df = conn.read(spreadsheet=url, ttl=0)
        
        st.write(f"### Historique : {label}")
        col_check, _ = st.columns([1, 2])
        with col_check:
            tout_afficher = st.checkbox(f"Afficher tout l'historique ({len(df)} lignes)", key=f"check_{spreadsheet_key}")
        
        if tout_afficher:
            st.dataframe(df, use_container_width=True)
        else:
            st.dataframe(df.tail(10), use_container_width=True)
            st.caption("Affichage des 10 dernières entrées.")
    except:
        st.warning(f"Impossible de charger les données pour {label}. Vérifiez l'URL et les accès.")

# --- INTERFACE PRINCIPALE ---
st.title("Collecte des données - Travaux pratiques physiologie végétale")

tab_eau, tab_photo = st.tabs(["Séance EAU", "Séance PHOTOSYNTHÈSE"])

# =================================================================
# ONGLET 1 : SÉANCE EAU
# =================================================================
with tab_eau:
    st.header("Mesures sur l'Eau")
    with st.form("form_eau", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            date_v = st.date_input("Date *", value=datetime.now())
            heure_v = st.time_input("Heure *", value=datetime.now())
            options_rang = ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12", "13-14", "15-16", "17-18", "19-20", "21-22", "23-24"]
            rang = st.selectbox("Rang feuille (#) *", options_rang, index=None, placeholder="Choisir...")
        with c2:
            etat = st.selectbox("Etat feuille *", ["Bien développée", "Jeune", "Vieille"], index=None, placeholder="Choisir...")
            pos = st.selectbox("Position limbe *", ["Base", "Milieu", "Pointe"], index=None, placeholder="Choisir...")
            face = st.selectbox("Face *", ["Abaxiale", "Adaxiale"], index=None, placeholder="Choisir...")
        with c3:
            cond = st.number_input("Conductance (mmol/m².s) *", format="%.2f", value=None)
            par = st.number_input("PAR (µmol/m².s)", format="%.1f", value=None)
        
        remarque = st.text_area("Remarque", key="rem_eau")
        submit = st.form_submit_button("Enregistrer Mesure Eau")

        if submit:
            if any(v is None for v in [rang, etat, pos, face, cond]):
                st.error("Veuillez remplir tous les champs obligatoires (*)")
            else:
                new_row = {
                    "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"),
                    "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                    "Rang feuille (#)": rang, "Etat feuille": etat,
                    "Position sur le limbre (Base-milieu-pointe)": pos,
                    "Face (Abaxiale-Adaxiale)": face,
                    "Conductance stomatique (mmol/m².s)": cond,
                    "PAR (µmol/m².s)": par, "Remarque": remarque
                }
                save_data("url_eau", new_row)

    visualiser_donnees("url_eau", "Séance Eau")

# =================================================================
# ONGLET 2 : SÉANCE PHOTOSYNTHÈSE
# =================================================================
with tab_photo:
    st.header("Mesures Photosynthèse")
    type_fichier = st.selectbox("Choisir l'appareil / type de mesure :", 
                                ["IRGA (Photosynthèse)", "Poromètre", "Croissance", "Fluorimètre"])
    
    st.divider()

    # --- 1. IRGA ---
    if type_fichier == "IRGA (Photosynthèse)":
        with st.form("form_irga", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                date_v = st.date_input("Date *", value=datetime.now())
                heure_v = st.time_input("Heure *", value=datetime.now())
                id_p = st.number_input("ID plante (1-20) *", 1, 20, value=None)
            with c2:
                c_in = st.number_input("CO2 in (ppm) *", value=None)
                c_out = st.number_input("CO2 out (ppm) *", value=None)
                h_in = st.number_input("H2O in (mbar) *", value=None)
                h_out = st.number_input("H2O out (mbar) *", value=None)
            with c3:
                qleaf = st.number_input("PAR (Qleaf) (µmol/m².s) *", value=None)
                pres = st.number_input("Pression (bar) *", value=None)
                temp = st.number_input("Température (°C) *", value=None)
                flux = st.number_input("Flux d'air (U) (µmol/s) *", value=None)
            with c4:
                a_val = st.number_input("A (µmol/m².s) *", value=None)
                e_val = st.number_input("E (mmol/m².s) *", value=None)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)
            
            remarque = st.text_area("Remarque", key="rem_irga")
            if st.form_submit_button("Enregistrer IRGA"):
                check_list = [id_p, c_in, c_out, h_in, h_out, qleaf, pres, temp, flux, a_val, e_val, trait]
                if any(v is None for v in check_list):
                    st.error("Champs obligatoires manquants")
                else:
                    new_row = {
                        "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"), "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                        "ID plante (1 - 20)": id_p, "CO2 in (Cref) (ppm)": c_in, "CO2 out (C'an) (ppm)": c_out,
                        "H2O in (eref) (mbar)": h_in, "H2O out (e'an) (mbar)": h_out, "PAR (Qleaf) (µmol/m².s)": qleaf,
                        "Pression (P) (bar)": pres, "Température (Tch) (°C)": temp, "Flux d'air (U) (µmol/s)": flux,
                        "A (µmol/m².s)": a_val, "E (mmol/m².s)": e_val, "Traitement (Lumière/Ombre)": trait, "Remarque": remarque
                    }
                    save_data("url_irga", new_row)
        visualiser_donnees("url_irga", "IRGA")

    # --- 2. POROMETRE ---
    elif type_fichier == "Poromètre":
        with st.form("form_poro", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                date_v = st.date_input("Date *", value=datetime.now())
                heure_v = st.time_input("Heure *", value=datetime.now())
                id_p = st.number_input("ID plante (1-20) *", 1, 20, value=None)
            with c2:
                gs = st.number_input("Gs (µmol eau/m².s) *", value=None)
                par = st.number_input("PAR (µmol de photons/m².s) *", value=None)
                app = st.selectbox("Appareil *", ["Lent", "Rapide"], index=None)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)
            
            remarque = st.text_area("Remarque", key="rem_poro")
            if st.form_submit_button("Enregistrer Poromètre"):
                if any(v is None for v in [id_p, gs, par, app, trait]):
                    st.error("Champs manquants")
                else:
                    new_row = {
                        "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"), "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                        "ID plante (1 - 20)": id_p, "Conductance stomatique (Gs) (µmol d'eau/m².s)": gs,
                        "Photosynthetically Active Radiation (PAR) (µmol de photons/m².s)": par,
                        "Type d'appareil (lent/rapide)": app, "Traitement (Lumière/Ombre)": trait, "Remarque": remarque
                    }
                    save_data("url_poro", new_row)
        visualiser_donnees("url_poro", "Poromètre")

    # --- 3. CROISSANCE ---
    elif type_fichier == "Croissance":
        with st.form("form_croissance", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                date_v = st.date_input("Date *", value=datetime.now())
                heure_v = st.time_input("Heure *", value=datetime.now())
                id_p = st.number_input("ID plante (1-20) *", 1, 20, value=None)
            with c2:
                h_tige = st.number_input("Hauteur tige (cm) *", value=None)
                n_feuilles = st.number_input("Nombre feuilles *", step=1, value=None)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)
            
            remarque = st.text_area("Remarque", key="rem_crois")
            if st.form_submit_button("Enregistrer Croissance"):
                if any(v is None for v in [id_p, h_tige, n_feuilles, trait]):
                    st.error("Champs manquants")
                else:
                    new_row = {
                        "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"), "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                        "ID plante (1 - 20)": id_p, "Hauteur de la tige (H, du pot au bourgeon terminal) (cm)": h_tige,
                        "Nombre de feuilles": n_feuilles, "Traitement (Ombre/Lumière)": trait, "Remarque": remarque
                    }
                    save_data("url_croissance", new_row)
        visualiser_donnees("url_croissance", "Croissance")

    # --- 4. FLUORIMETRE ---
    elif type_fichier == "Fluorimètre":
        with st.form("form_fluo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                date_v = st.date_input("Date *", value=datetime.now())
                heure_v = st.time_input("Heure *", value=datetime.now())
                id_p = st.number_input("ID plante (1-20) *", 1, 20, value=None)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)
            with c2:
                y_ii = st.number_input("Y_II *", format="%.4f", value=None)
                fv_fm = st.number_input("Fv/Fm", format="%.4f", value=None)
                y_npq = st.number_input("Y(NPQ)", format="%.4f", value=None)
                y_no = st.number_input("Y(NO)", format="%.4f", value=None)
                a_par = st.number_input("Actinic PAR", value=None)
            
            remarque = st.text_area("Remarque", key="rem_fluo")
            if st.form_submit_button("Enregistrer Fluorimètre"):
                if any(v is None for v in [id_p, trait, y_ii]):
                    st.error("Champs manquants")
                else:
                    new_row = {
                        "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"), "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                        "ID plante (1 - 20)": id_p, "Traitement (Ombre/Lumière)": trait,
                        "Y_II": y_ii, "Fv/Fm": fv_fm, "Y(NPQ)": y_npq, "Y(NO)": y_no,
                        "Actinic PAR": a_par, "Remarque": remarque
                    }
                    save_data("url_fluo", new_row)
        visualiser_donnees("url_fluo", "Fluorimètre")
