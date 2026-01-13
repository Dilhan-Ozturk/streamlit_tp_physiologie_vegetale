import gspread
import io
import pytz

import pandas as pd
import streamlit as st

from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials

# Définition de quelques constantes
TITLE = "LBIR1251 - Travaux pratiques : collecte des données"
TIME_ZONE = pytz.timezone('Europe/Brussels')

# Configuration de la page
st.set_page_config(page_title=TITLE, layout="wide")

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

# --- FONCTION : VISUALISATION & TÉLÉCHARGEMENT ---
def show_data(spreadsheet_key, label):
    try:
        url = st.secrets["connections"]["gsheets"][spreadsheet_key]
        df = conn.read(spreadsheet=url, ttl=0)

        st.write(f"### Historique : {label}")
        
        # Création de deux colonnes pour les options et le téléchargement
        col_opts, col_dl_csv, col_dl_excel = st.columns([1, 1, 1])
        
        with col_opts:
            tout_afficher = st.checkbox(f"Afficher tout l'historique ({len(df)} lignes)", key=f"check_{spreadsheet_key}")
        
        with col_dl_csv:
            # Préparation du fichier CSV pour le téléchargement
            # on utilise utf-8-sig pour que les accents s'affichent bien dans Excel
            csv = df.to_csv(index=False).encode('utf-8-sig')

            st.download_button(
                label="📥 Télécharger en format .csv",
                data=csv,
                file_name=f"export_{label.replace(' ', '_').lower()}_{datetime.now(TIME_ZONE).strftime('%d_%m_%Y')}.csv",
                mime='text/csv',
                key=f"btn_{spreadsheet_key}_csv"
            )

        with col_dl_excel:
            buffer = io.BytesIO()

            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
                writer.close()
                st.download_button(
                    label="📥 Télécharger en format .xlsx",
                    data=buffer,
                    file_name=f"export_{label.replace(' ', '_').lower()}_{datetime.now(TIME_ZONE).strftime('%d_%m_%Y')}.xlsx",
                    mime='application/vnd.ms-excel',
                    key = f"btn_{spreadsheet_key}_excel"
                )

        if tout_afficher:
            st.dataframe(df, use_container_width=True)
        else:
            st.dataframe(df.tail(10), use_container_width=True)
            st.caption("Affichage des 10 dernières entrées.")
            
    except Exception as e:
        st.warning(f"Impossible de charger les données pour {label}. Vérifiez l'URL et les accès. Erreur: {e}")


# --- INTERFACE PRINCIPALE ---
st.title(TITLE)

HEADER_TP_EAU = "TP1 : l'eau"
HEADER_TP_PHOTOSYNTHESE = "TP5 : la photosynthèse"
HEADER_TP_TOURNESOL = "Votre tournesol"

tab_eau, tab_photo, tab_tournesol = st.tabs([HEADER_TP_EAU,
                                             HEADER_TP_PHOTOSYNTHESE,
                                             HEADER_TP_TOURNESOL])

# =================================================================
# ONGLET 1 : SÉANCE EAU
# =================================================================
with tab_eau:
    st.header(HEADER_TP_EAU)

    with st.form("form_eau", clear_on_submit=True):
        st.write("### Poromètre : ajouter une mesure")

        c1, c2, c3 = st.columns(3)
        with c1:
            date_v = st.date_input("Date de la mesure *", format="DD/MM/YYYY", value=datetime.now(TIME_ZONE))
            heure_v = st.time_input("Heure de la mesure*", value=datetime.now(TIME_ZONE))
            options_rang = ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12", "13-14", "15-16", "17-18", "19-20", "21-22", "23-24"]
            rang = st.selectbox("Rang de la feuille *", options_rang, index=None, placeholder="Choisir...")
        with c2:
            etat = st.selectbox("État de la feuille *", ["Bien développée", "Jeune", "Vieille"], index=None, placeholder="Choisir...")
            pos = st.selectbox("Position sur le limbe *", ["Base", "Milieu", "Pointe"], index=None, placeholder="Choisir...")
            face = st.selectbox("Face de la feuille *", ["Abaxiale", "Adaxiale"], index=None, placeholder="Choisir...")
        with c3:
            cond = st.number_input("Conductance stomatique (mmol/m².s) *", format="%.2f", value=None, step=0.01)
            par = st.number_input("PAR (µmol/m².s)", format="%.2f", value=None, step=0.01)
        
        remarque = st.text_area("Remarque", key="rem_eau")
        submit = st.form_submit_button("Enregistrer")

        if submit:
            if any(v is None for v in [rang, etat, pos, face, cond]):
                st.error("Veuillez remplir tous les champs obligatoires (*)")
            else:
                new_row = {
                    "date": date_v.strftime("%d/%m/%Y"),
                    "heure": heure_v.strftime("%H:%M"),
                    "rang_f": rang,
                    "état_f": etat,
                    "pos_f": pos,
                    "face_f": face,
                    "cond": cond,
                    "PAR": par,
                    "remarque": remarque
                }

                save_data("url_eau", new_row)

    show_data("url_eau", "poromètre")

# =================================================================
# ONGLET 2 : SÉANCE PHOTOSYNTHÈSE
# =================================================================
with tab_photo:
    st.header(HEADER_TP_PHOTOSYNTHESE)

    type_fichier = st.selectbox("Choisir l'appareil ou le type type de mesure :",
                                ["IRGA", "Poromètre", "Croissance", "Fluorimètre"])
    
    st.divider()

    # --- 1. IRGA ---
    if type_fichier == "IRGA":
        st.write("### IRGA : ajouter une mesure")

        with st.form("form_irga", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                date_v = st.date_input("Date de la mesure *", format="DD/MM/YYYY", value=datetime.now(TIME_ZONE))
                heure_v = st.time_input("Heure de la mesure*", value=datetime.now(TIME_ZONE))
                id_p = st.number_input("ID plante (1-20) *", 1, 20, value=None, step=1)

            with c2:
                c_in = st.number_input("CO2 in (ppm) *", value=None, step=1)
                c_out = st.number_input("CO2 out (ppm) *", value=None, step=1)
                h_in = st.number_input("H2O in (mbar) *", value=None, step=0.1)
                h_out = st.number_input("H2O out (mbar) *", value=None, step=0.1)

            with c3:
                qleaf = st.number_input("PAR (Qleaf) (µmol/m².s) *", value=None, step=0.01)
                pres = st.number_input("Pression (bar) *", value=None, step=0.01)
                temp = st.number_input("Température (°C) *", value=None, step=0.1)
                flux = st.number_input("Flux d'air (U) (µmol/s) *", value=None, step=0.01)

            with c4:
                a_val = st.number_input("A (µmol/m².s) *", value=None, step=0.01)
                e_val = st.number_input("E (mmol/m².s) *", value=None, step=0.01)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)
            
            remarque = st.text_area("Remarque", key="rem_irga")

            if st.form_submit_button("Enregistrer"):
                check_list = [id_p, c_in, c_out, h_in, h_out, qleaf, pres, temp, flux, a_val, e_val, trait]
                if any(v is None for v in check_list):
                    st.error("Champs obligatoires manquants")
                else:
                    new_row = {
                        "date": date_v.strftime("%d/%m/%Y"),
                        "heure": heure_v.strftime("%H:%M"),
                        "plante_ID": id_p,
                        "CO2_in": c_in,
                        "CO2_out": c_out,
                        "H2O_in": h_in,
                        "H2O_out": h_out,
                        "PAR": qleaf,
                        "pression": pres,
                        "temp": temp,
                        "flux_air": flux,
                        "A": a_val,
                        "E": e_val,
                        "traitement": trait,
                        "remarque": remarque
                    }

                    save_data("url_irga", new_row)

        show_data("url_irga", "IRGA")

    # --- 2. POROMETRE ---
    elif type_fichier == "Poromètre":
        st.write("### Poromètre : ajouter une mesure")

        with st.form("form_poro", clear_on_submit=True):
            c1, c2 = st.columns(2)

            with c1:
                date_v = st.date_input("Date de la mesure *", format="DD/MM/YYYY", value=datetime.now(TIME_ZONE))
                heure_v = st.time_input("Heure de la mesure *", value=datetime.now(TIME_ZONE))
                id_p = st.number_input("ID plante (1-20) *", 1, 20, value=None, step=1)

            with c2:
                gs = st.number_input("Conductance stomatique (µmol/m².s) *", value=None, step=0.1)
                par = st.number_input("PAR (µmol/m².s) *", value=None, step=0.01)
                app = st.selectbox("Appareil *", ["Lent", "Rapide"], index=None)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)
            
            remarque = st.text_area("Remarque", key="rem_poro")

            if st.form_submit_button("Enregistrer"):
                if any(v is None for v in [id_p, gs, par, app, trait]):
                    st.error("Champs manquants")
                else:
                    new_row = {
                        "date": date_v.strftime("%d/%m/%Y"),
                        "heure": heure_v.strftime("%H:%M"),
                        "plante_ID": id_p,
                        "cond": gs,
                        "PAR": par,
                        "type_appareil": app,
                        "traitement": trait,
                        "remarque": remarque
                    }

                    save_data("url_poro", new_row)

        show_data("url_poro", "poromètre")

    # --- 3. CROISSANCE ---
    elif type_fichier == "Croissance":
        st.write("### Croissance : ajouter une mesure")

        with st.form("form_croissance", clear_on_submit=True):
            c1, c2 = st.columns(2)

            with c1:
                date_v = st.date_input("Date de la mesure *", format="DD/MM/YYYY", value=datetime.now(TIME_ZONE))
                heure_v = st.time_input("Heure de la mesure *", value=datetime.now(TIME_ZONE))
                id_p = st.number_input("ID plante (1-20) *", 1, 20, value=None, step=1)

            with c2:
                h_tige = st.number_input("Hauteur de la tige (cm) *", value=None, step=0.1)
                n_feuilles = st.number_input("Nombre de feuilles *", step=1, value=None)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)
            
            remarque = st.text_area("Remarque", key="rem_crois")

            if st.form_submit_button("Enregistrer"):
                if any(v is None for v in [id_p, h_tige, n_feuilles, trait]):
                    st.error("Champs manquants")
                else:
                    new_row = {
                        "date": date_v.strftime("%d/%m/%Y"),
                        "heure": heure_v.strftime("%H:%M"),
                        "plante_ID": id_p,
                        "hauteur_tige": h_tige,
                        "n_feuilles": n_feuilles,
                        "traitement": trait,
                        "remarque": remarque
                    }

                    save_data("url_croissance", new_row)

        show_data("url_croissance", "croissance")

    # --- 4. FLUORIMETRE ---
    elif type_fichier == "Fluorimètre":
        st.write("### Fluorimètre : ajouter une mesure")

        with st.form("form_fluo", clear_on_submit=True):
            c1, c2 = st.columns(2)

            with c1:
                date_v = st.date_input("Date de la mesure *", format="DD/MM/YYYY", value=datetime.now(TIME_ZONE))
                heure_v = st.time_input("Heure de la mesure *", value=datetime.now(TIME_ZONE))
                id_p = st.number_input("ID plante (1-20) *", 1, 20, value=None, step=1)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)

            with c2:
                y_ii = st.number_input("Y_II *", format="%.3f", value=None, step=0.001)
                fv_fm = st.number_input("Fv/Fm", format="%.3f", value=None, step=0.001)
                y_npq = st.number_input("Y(NPQ)", format="%.3f", value=None, step=0.001)
                y_no = st.number_input("Y(NO)", format="%.3f", value=None, step=0.001)
                a_par = st.number_input("Actinic PAR", value=None, step=1)
            
            remarque = st.text_area("Remarque", key="rem_fluo")

            if st.form_submit_button("Enregistrer"):
                if any(v is None for v in [id_p, trait, y_ii]):
                    st.error("Champs manquants")
                else:
                    new_row = {
                        "date": date_v.strftime("%d/%m/%Y"),
                        "heure": heure_v.strftime("%H:%M"),
                        "plante_ID": id_p,
                        "traitement": trait,
                        "Y_II": y_ii,
                        "Fv/Fm": fv_fm,
                        "Y(NPQ)": y_npq,
                        "Y(NO)": y_no,
                        "act_PAR": a_par,
                        "remarque": remarque
                    }

                    save_data("url_fluo", new_row)

        show_data("url_fluo", "fluorimètre")
