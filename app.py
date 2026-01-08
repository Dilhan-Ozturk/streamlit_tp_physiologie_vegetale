import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Physiologie Végétale - Collecte des données", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FONCTION DE SAUVEGARDE GÉNÉRIQUE ---
def save_data(spreadsheet_key, new_row_dict):
    url = st.secrets["connections"]["gsheets"][spreadsheet_key]
    existing_df = conn.read(spreadsheet=url)
    new_df = pd.concat([existing_df, pd.DataFrame([new_row_dict])], ignore_index=True)
    conn.update(spreadsheet=url, data=new_df)
    st.success("Données enregistrées avec succès !")
    st.balloons()

# --- STRUCTURE DES ONGLETS ---
tab_eau, tab_photo = st.tabs(["Séance : Eau", "Séance : Photosynthèse"])

# ==========================================
# ONGLET 1 : SÉANCE EAU
# ==========================================
with tab_eau:
    st.header("Mesures : Eau")
    with st.form("form_eau", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date_v = st.date_input("Date", value=datetime.now())
            heure_v = st.time_input("Heure", value=datetime.now())
            rang = st.number_input("Rang feuille (#)", min_value=1, step=1)
            etat = st.selectbox("Etat feuille", ["Saine", "Sénescente", "Malade"])
        with col2:
            pos = st.selectbox("Position sur le limbre", ["Base", "Milieu", "Pointe"])
            face = st.selectbox("Face", ["Abaxiale", "Adaxiale"])
            cond = st.number_input("Conductance stomatique (mmol/m².s)", format="%.2f")
            par = st.number_input("PAR (µmol/m².s)", format="%.1f")
        
        remarque = st.text_area("Remarque (Optionnel)")
        submit = st.form_submit_button("Enregistrer Eau")

        if submit:
            new_row = {
                "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"),
                "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                "Rang feuille (#)": rang,
                "Etat feuille": etat,
                "Position sur le limbre (Base-milieu-pointe)": pos,
                "Face (Abaxiale-Adaxiale)": face,
                "Conductance stomatique (mmol/m².s)": cond,
                "PAR (µmol/m².s)": par,
                "Remarque": remarque
            }
            save_data("url_eau", new_row)

# ==========================================
# ONGLET 2 : SÉANCE PHOTOSYNTHÈSE
# ==========================================
with tab_photo:
    st.header("Mesures : Photosynthèse")
    
    type_mesure = st.selectbox("Choisir le type de mesure :", 
                              ["IRGA (Echanges gazeux)", "Poromètre", "Croissance", "Fluorimètre"])
    
    st.divider()

    # --- SOUS-SECTION 1 : IRGA ---
    if type_mesure == "IRGA (Echanges gazeux)":
        with st.form("form_irga", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                date_v = st.date_input("Date *", value=datetime.now())
                heure_v = st.time_input("Heure *", value=datetime.now())
                id_p = st.number_input("ID plante (1-20) *", 1, 20)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"])
            with c2:
                co2_in = st.number_input("CO2 in (Cref) (ppm) *", format="%.2f")
                co2_out = st.number_input("CO2 out (C'an) (ppm) *", format="%.2f")
                h2o_in = st.number_input("H2O in (eref) (mbar) *", format="%.2f")
                h2o_out = st.number_input("H2O out (e'an) (mbar) *", format="%.2f")
            with c3:
                par_irga = st.number_input("PAR (Qleaf) (µmol/m².s) *", format="%.1f")
                pres = st.number_input("Pression (P) (bar) *", format="%.3f")
                temp = st.number_input("Température (Tch) (°C) *", format="%.1f")
                flux = st.number_input("Flux d'air (U) (µmol/s) *", format="%.1f")
            
            c4, c5 = st.columns(2)
            with c4: a_val = st.number_input("A (µmol/m².s) *", format="%.2f")
            with c5: e_val = st.number_input("E (mmol/m².s) *", format="%.2f")
            
            remarque = st.text_area("Remarque (Optionnel)", key="rem_irga")
            
            if st.form_submit_button("Enregistrer IRGA"):
                new_row = {
                    "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"), "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                    "ID plante (1 - 20)": id_p, "CO2 in (Cref) (ppm)": co2_in, "CO2 out (C'an) (ppm)": co2_out,
                    "H2O in (eref) (mbar)": h2o_in, "H2O out (e'an) (mbar)": h2o_out, "PAR (Qleaf) (µmol/m².s)": par_irga,
                    "Pression (P) (bar)": pres, "Température (Tch) (°C)": temp, "Flux d'air (U) (µmol/s)": flux,
                    "A (µmol/m².s)": a_val, "E (mmol/m².s)": e_val, "Traitement (Lumière/Ombre)": trait, "Remarque": remarque
                }
                save_data("url_irga", new_row)

    # --- SOUS-SECTION 2 : POROMÈTRE ---
    elif type_mesure == "Poromètre":
        with st.form("form_poro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date_v = st.date_input("Date *", value=datetime.now())
                heure_v = st.time_input("Heure *", value=datetime.now())
                id_p = st.number_input("ID plante (1-20) *", 1, 20)
            with col2:
                gs = st.number_input("Conductance stomatique (Gs) (µmol d'eau/m².s) *", format="%.2f")
                par_p = st.number_input("PAR (µmol de photons/m².s) *", format="%.1f")
                type_app = st.selectbox("Type d'appareil *", ["lent", "rapide"])
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"])
            
            remarque = st.text_area("Remarque (Optionnel)", key="rem_poro")
            if st.form_submit_button("Enregistrer Poromètre"):
                new_row = {
                    "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"), "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                    "ID plante (1 - 20)": id_p, "Conductance stomatique (Gs) (µmol d'eau/m².s)": gs,
                    "Photosynthetically Active Radiation (PAR) (µmol de photons/m².s)": par_p,
                    "Type d'appareil (lent/rapide)": type_app, "Traitement (Lumière/Ombre)": trait, "Remarque": remarque
                }
                save_data("url_poro", new_row)

    # --- SOUS-SECTION 3 : CROISSANCE ---
    elif type_mesure == "Croissance":
        with st.form("form_croissance", clear_on_submit=True):
            date_v = st.date_input("Date *", value=datetime.now())
            heure_v = st.time_input("Heure *", value=datetime.now())
            id_p = st.number_input("ID plante (1-20) *", 1, 20)
            hauteur = st.number_input("Hauteur de la tige (cm) *", format="%.1f")
            nb_f = st.number_input("Nombre de feuilles *", min_value=0, step=1)
            trait = st.selectbox("Traitement *", ["Lumière", "Ombre"])
            remarque = st.text_area("Remarque (Optionnel)", key="rem_croiss")
            
            if st.form_submit_button("Enregistrer Croissance"):
                new_row = {
                    "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"), "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                    "ID plante (1 - 20)": id_p, "Hauteur de la tige (H, du pot au bourgeon terminal) (cm)": hauteur,
                    "Nombre de feuilles": nb_f, "Traitement (Ombre/Lumière)": trait, "Remarque": remarque
                }
                save_data("url_croissance", new_row)

    # --- SOUS-SECTION 4 : FLUORIMÈTRE ---
    elif type_mesure == "Fluorimètre":
        with st.form("form_fluo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                date_v = st.date_input("Date *", value=datetime.now())
                heure_v = st.time_input("Heure *", value=datetime.now())
                id_p = st.number_input("ID plante (1-20) *", 1, 20)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"])
            with c2:
                y_ii = st.number_input("Y_II *", format="%.4f")
                fv_fm = st.number_input("Fv/Fm *", format="%.4f")
                y_npq = st.number_input("Y(NPQ) *", format="%.4f")
                y_no = st.number_input("Y(NO) *", format="%.4f")
                a_par = st.number_input("Actinic PAR *", format="%.1f")
            
            remarque = st.text_area("Remarque (Optionnel)", key="rem_fluo")
            if st.form_submit_button("Enregistrer Fluorimètre"):
                new_row = {
                    "Date (jj/mm/yyyy)": date_v.strftime("%d/%m/%Y"), "Heure (hh:mm)": heure_v.strftime("%H:%M"),
                    "ID plante (1 - 20)": id_p, "Traitement (Ombre/Lumière)": trait,
                    "Y_II": y_ii, "Fv/Fm": fv_fm, "Y(NPQ)": y_npq, "Y(NO)": y_no, 
                    "Actinic PAR": a_par, "Remarque": remarque
                }
                save_data("url_fluo", new_row)
