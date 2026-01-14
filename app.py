import gspread
import io
import pytz
import pandas as pd
import streamlit as st
from datetime import datetime
from google.oauth2.service_account import Credentials

# --- CONFIGURATION & CONSTANTES ---
TITLE = "LBIR1251 - Travaux pratiques : collecte des données"
TIME_ZONE = pytz.timezone('Europe/Brussels')
st.set_page_config(page_title=TITLE, layout="wide")

# Noms des secrets/clés pour Google Sheets
INSCRIPTION = 'inscription'
PIECE = 'piece'
OBS_PLANTE = 'obs_plante'
OBS_FEUILLE = 'obs_feuille'

# --- FONCTION : LECTURE (AVEC CACHE) ---
@st.cache_data(ttl=60)
def get_df_from_url(url_key):
    """Lit un Google Sheet à partir de sa clé dans les secrets et retourne un DataFrame"""
    try:
        sks = st.secrets["connections"]["gsheets"]
        creds = Credentials.from_service_account_info(sks, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        gc = gspread.authorize(creds)
        url = sks.get(url_key, url_key) 
        data = gc.open_by_url(url).sheet1.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erreur de lecture ({url_key}): {e}")
        return pd.DataFrame()

# --- FONCTION : SAUVEGARDE ---
def save_data(spreadsheet_key, new_row_dict):
    try:
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
            "client_x509_cert_url": sks.get("client_x509_cert_url")
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        url = sks[spreadsheet_key]
        sheet = client.open_by_url(url).sheet1
        sheet.append_row(list(new_row_dict.values()))
        
        st.toast("Données enregistrées !", icon="✅")
        # On vide le cache pour que la nouvelle ligne soit visible au prochain affichage
        st.cache_data.clear()
        
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")

# --- FONCTION : VISUALISATION ---
def show_data(spreadsheet_key, label):
    df = get_df_from_url(spreadsheet_key)
    if df.empty:
        st.info(f"Aucune donnée pour {label}.")
        return

    st.write(f"### Historique : {label}")
    col_opts, col_dl_csv, col_dl_excel = st.columns([1, 1, 1])
    
    with col_opts:
        tout_afficher = st.checkbox(f"Afficher tout ({len(df)} lignes)", key=f"check_{spreadsheet_key}")
    
    with col_dl_csv:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 .csv", data=csv, file_name=f"{label}.csv", mime='text/csv', key=f"csv_{spreadsheet_key}")

    with col_dl_excel:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 .xlsx", data=buffer, file_name=f"{label}.xlsx", key=f"xlsx_{spreadsheet_key}")

    if tout_afficher:
        st.dataframe(df, use_container_width=True)
    else:
        st.dataframe(df.tail(10), use_container_width=True)
        st.caption("Affichage des 10 dernières entrées.")

# --- INTERFACE PRINCIPALE ---
st.title(TITLE)
tab_eau, tab_photo, tab_tournesol = st.tabs(["TP1 : l'eau", "TP5 : la photosynthèse", "Votre tournesol"])
MANDATORY_FIELDS_MISSING = "Veuillez remplir tous les champs obligatoires marqués d'un *"

# --- ONGLET 1 : EAU ---
with tab_eau:
    st.header("TP1 : l'eau")
    with st.form("form_eau", clear_on_submit=True):
        st.write("### Poromètre : ajouter une mesure")
        c1, c2, c3 = st.columns(3)
        with c1:
            date_v = st.date_input("Date *", format="DD/MM/YYYY", value=datetime.now(TIME_ZONE))
            heure_v = st.time_input("Heure *", value=datetime.now(TIME_ZONE))
            rang = st.selectbox("Rang de la feuille *", ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12"], index=None)
        with c2:
            etat = st.selectbox("État *", ["Bien développée", "Jeune", "Vieille"], index=None)
            pos = st.selectbox("Position *", ["Base", "Milieu", "Pointe"], index=None)
            face = st.selectbox("Face *", ["Abaxiale", "Adaxiale"], index=None)
        with c3:
            cond = st.number_input("Conductance (mmol/m².s) *", format="%.2f", value=None)
            par = st.number_input("PAR (µmol/m².s)", format="%.2f", value=None)
        
        remarque = st.text_area("Remarque", key="rem_eau")
        if st.form_submit_button("Enregistrer"):
            if any(v is None for v in [rang, etat, pos, face, cond]):
                st.error(MANDATORY_FIELDS_MISSING)
            else:
                save_data("url_eau", {"date": date_v.strftime("%d/%m/%Y"), "heure": heure_v.strftime("%H:%M"), "rang": rang, "etat": etat, "pos": pos, "face": face, "cond": cond, "par": par, "rem": remarque})
    show_data("url_eau", "poromètre")

# --- ONGLET 2 : PHOTOSYNTHÈS --- (Version simplifiée pour la review)
with tab_photo:
    st.header("TP5 : la photosynthèse")
    type_f = st.selectbox("Appareil :", ["IRGA", "Poromètre", "Croissance", "Fluorimètre"])
    # Les formulaires IRGA/Poro/Croissance/Fluo restent identiques à votre code initial
    # ... (Gardez votre logique de conditions if type_fichier == "IRGA" etc.)

# --- ONGLET 3 : TOURNESOL ---
with tab_tournesol:
    st.header("Votre tournesol")
    st.info("Suivi de croissance S2 à S11")

    FORM_TOURNESOL = {
        INSCRIPTION : "Inscrire mon tournesol",
        PIECE : "Caractéristiques de la pièce",
        OBS_PLANTE : "Observations plante entière (hebdomadaire)",
        OBS_FEUILLE : "Observations feuilles (fin d'expérience)"
    }
    form_selector = st.selectbox("Action :", list(FORM_TOURNESOL.values()))

    # Chargement des bases de données nécessaires pour l'onglet
    df_eleves = get_df_from_url('listing_etudiants')
    df_inscrits = get_df_from_url(INSCRIPTION)

    if form_selector == FORM_TOURNESOL[INSCRIPTION]:
        with st.form(INSCRIPTION, clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                etudiant = st.selectbox("Étudiant·e", df_eleves.agg(lambda x: f"{x['nom']} {x['prénom']} - {x['NOMA']:.0f}", axis=1), index=None)
                second_t = st.checkbox("2ème tournesol (si le 1er est mort)")
            with col2:
                date_r = st.date_input("Date réception", value=datetime.now(TIME_ZONE))
            rem = st.text_area("Remarque")
            if st.form_submit_button("Enregistrer"):
                if etudiant:
                    noma = etudiant.split(' - ')[1]
                    if second_t: noma += "_B"
                    save_data(INSCRIPTION, {"plante_ID": noma, "date": date_r.strftime("%d/%m/%Y"), "rem": rem})
        show_data(INSCRIPTION, "tournesols")

    elif form_selector == FORM_TOURNESOL[PIECE]:
        with st.form(PIECE, clear_on_submit=True):
            plante_id = st.selectbox("ID Tournesol *", df_inscrits['plante_ID'] if not df_inscrits.empty else [], index=None)
            # ... Vos champs distance, orientation, etc.
            if st.form_submit_button("Enregistrer"):
                if plante_id:
                    # save_data(PIECE, {...})
                    pass
        show_data(PIECE, "pièces")

    # Même logique pour OBS_PLANTE et OBS_FEUILLE...
