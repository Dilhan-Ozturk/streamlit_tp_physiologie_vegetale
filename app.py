import gspread
import io
import pytz
import pandas as pd
import streamlit as st
from datetime import datetime
from google.oauth2.service_account import Credentials

# Définition de quelques constantes
TITLE = "LBIR1251 - Travaux pratiques : collecte des données"
TIME_ZONE = pytz.timezone('Europe/Brussels')
st.set_page_config(page_title=TITLE, layout="wide")

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
        
        # On vide le cache pour que la nouvelle ligne soit visible au prochain affichage
        st.cache_data.clear()
        
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")

# --- FONCTION : VISUALISATION & TÉLÉCHARGEMENT ---
def show_data(spreadsheet_key, label):
    st.write(f"### Historique : {label}")
    
    unique_key = f"check_{spreadsheet_key}_{label.replace(' ', '_')}"

    show_historical_data = st.checkbox(
        f"Afficher/Actualiser le tableau des {label}", 
        key=unique_key
    )
    
    if show_historical_data:
        with st.spinner(f"Chargement des {label}..."):
            try:
                # Connexion via gspread
                df = get_df_from_url(spreadsheet_key)
        
                if df.empty:
                    st.info("Aucune donnée enregistrée pour le moment.")
                    return
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
                        # -> UserWarning: Calling close() on already closed file.
                        # MAIS, retirer writer.close() produit des fichiers excels corrompus.
                        writer.close()
                        st.download_button(
                            label="📥 Télécharger en format .xlsx",
                            data=buffer,
                            file_name=f"export_{label.replace(' ', '_').lower()}_{datetime.now(TIME_ZONE).strftime('%d_%m_%Y')}.xlsx",
                            mime='application/vnd.ms-excel',
                            key = f"btn_{spreadsheet_key}_excel"
                        )
        
                if tout_afficher:
                    st.dataframe(df, width="stretch")
                else:
                    st.dataframe(df.tail(10), width="stretch")
                    st.caption("Affichage des 10 dernières entrées.")
                    
            except Exception as e:
                st.warning(f"Impossible de charger les données pour {label}. Vérifiez l'URL et les accès. Erreur: {e}")
    else:
        st.info("Cochez la case ci-dessus pour afficher les données encodées.")


# --- INTERFACE PRINCIPALE ---
st.title(TITLE)

HEADER_TP_EAU = "TP1 : l'eau"
HEADER_TP_PHOTOSYNTHESE = "TP5 : la photosynthèse"
HEADER_TP_TOURNESOL = "Votre tournesol"

MANDATORY_FIELDS_MISSING = "Veuillez remplir tous les champs obligatoires marqués d'un *"

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
        with c2:
            rang = st.number_input("Rang de la feuille *", step=1, min_value=1,
                                   help="Numéro d'ordre de la feuille (par ordre d'apparition). La feuille la plus "
                                        "âgée (rang 1) est la feuille la plus basse alors que la feuille la plus "
                                        "récente (rang élevé) est celle qui se trouve le plus haut. Chez le tournesol, "
                                        "les premières feuilles sont parfois opposées. Dans ce cas, vous pouvez les "
                                        "numéroter 1 et 2 au hasard, puis 3 et 4 au hasard.")
            face = st.selectbox("Face de la feuille *", ["Abaxiale", "Adaxiale"], index=None, placeholder="Choisir...")
            etat = st.selectbox("État de la feuille *", ["Bien développée", "Jeune", "Vieille"], index=None, placeholder="Choisir...")
        with c3:
            cond = st.number_input("Conductance stomatique (mmol/m².s) *", format="%.2f", value=None, step=0.01,
                                   min_value=0.0, max_value=1200.0)
            par = st.number_input("PAR (µmol/m².s)", format="%.2f", value=None, step=0.01,
                                  min_value=0.0, max_value=2500.0)
        
        remarque = st.text_area("Remarque", key="rem_eau")
        submit = st.form_submit_button("Enregistrer")

        if submit:
            if any(v is None for v in [rang, etat, face, cond]):
                st.error(MANDATORY_FIELDS_MISSING)
            else:
                new_row = {
                    "date": date_v.strftime("%d/%m/%Y"),
                    "heure": heure_v.strftime("%H:%M"),
                    "rang_f": rang,
                    "état_f": etat,
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
                                ["IRGA", "Poromètre", "Croissance", "Fluorimètre", "Chlorophyllomètre"])
    
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
                    st.error(MANDATORY_FIELDS_MISSING)
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
                gs = st.number_input("Conductance stomatique [mol/m².s] *", value=None, step=0.1,
                                     min_value=0.0, max_value=1200.0)
                par = st.number_input("PAR (Qamb) [µmol/m².s] *", value=None, step=0.01,
                                      min_value=0.0, max_value=2500.0)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)
            
            remarque = st.text_area("Remarque", key="rem_poro")

            if st.form_submit_button("Enregistrer"):
                if any(v is None for v in [id_p, gs, par, trait]):
                    st.error(MANDATORY_FIELDS_MISSING)
                else:
                    new_row = {
                        "date": date_v.strftime("%d/%m/%Y"),
                        "heure": heure_v.strftime("%H:%M"),
                        "plante_ID": id_p,
                        "cond": gs,
                        "PAR": par,
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
                    st.error(MANDATORY_FIELDS_MISSING)
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
                a_par = st.number_input("Actinic PAR", value=None, step=1)
            
            remarque = st.text_area("Remarque", key="rem_fluo")

            if st.form_submit_button("Enregistrer"):
                if any(v is None for v in [id_p, trait, y_ii]):
                    st.error(MANDATORY_FIELDS_MISSING)
                else:
                    new_row = {
                        "date": date_v.strftime("%d/%m/%Y"),
                        "heure": heure_v.strftime("%H:%M"),
                        "plante_ID": id_p,
                        "traitement": trait,
                        "Y_II": y_ii,
                        "act_PAR": a_par,
                        "remarque": remarque
                    }

                    save_data("url_fluo", new_row)

        show_data("url_fluo", "fluorimètre")
    elif type_fichier == "Chlorophyllomètre":
        st.write("### Chlorophyllomètre : ajouter une mesure")

        with st.form("form_chloro", clear_on_submit=True):
            c1, c2 = st.columns(2)

            with c1:
                date_v = st.date_input("Date de la mesure *", format="DD/MM/YYYY", value=datetime.now(TIME_ZONE))
                heure_v = st.time_input("Heure de la mesure *", value=datetime.now(TIME_ZONE))
                id_p = st.number_input("ID plante (1-20) *", 1, 20, value=None, step=1)
                trait = st.selectbox("Traitement *", ["Lumière", "Ombre"], index=None)

            with c2:
                appareil = st.selectbox("Appareil *", ["Neuf", "Vieux"], index=None)
                CCI = st.number_input("Chlorophyll Content Index (CCI) *", format="%.3f", value=None, step=0.001)
                PAR = st.number_input("PAR [µmol/m²/s] *", format="%.3f", value=None, step=0.001)

            if st.form_submit_button("Enregistrer"):
                if any(v is None for v in [id_p, trait, appareil, CCI, PAR]):
                    st.error(MANDATORY_FIELDS_MISSING)
                else:
                    new_row = {
                        "date": date_v.strftime("%d/%m/%Y"),
                        "heure": heure_v.strftime("%H:%M"),
                        "plante_ID": id_p,
                        "traitement": trait,
                        "appareil": appareil,
                        "CCI": CCI,
                        "PAR": PAR,
                    }

                    save_data("url_chloro", new_row)

        show_data("url_chloro", "chlorophyllomètre")

with tab_tournesol:
    st.header(HEADER_TP_TOURNESOL)

    st.markdown('''
        Pour étudier l'influence de l'environnement sur la croissance et le développement des plantes, vous allez
        observer un tournesol :sunflower:. Vous recevrez votre tournesol lors du **TP1** (en S2 ou S3) et l'observerez
        jusqu'en S11. Au **TP8** (en S12), nous analyserons l'ensemble des données collectées.

        :blue-background[Cette page permet l'encodage de toutes les données nécessaires].

        Le sélecteur ci-dessous vous permet :
        * d'inscrire votre tournesol à l'expérience : :red[à faire **une seule fois** en début d'expérience] (sauf si votre tournesol
        meurt en cours d'expérience) ;
        * d'indiquer les caractéristiques de la pièce dans laquelle se trouve votre tournesol : :red[à faire **une seule fois**
        après avoir caractérisé votre pièce] ;
        * d'ajouter des observations sur la plante entière (stade, hauteur) : :red[à faire **chaque semaine**];
        * d'ajouter des observations sur les feuilles de votre tournesol (longueur, largeur) : :red[à faire **une seule fois**
        à **la fin** de l'expérience].
        
        Bon encodage ! :balloon:
        
        ---
        '''
    )

    FORM_TOURNESOL = {
        INSCRIPTION : "Inscrire mon tournesol",
        PIECE : "Indiquer les caractéristiques de la pièce dans laquelle se trouve mon tournesol",
        OBS_PLANTE : "Ajouter des observations sur la plante entière (stade, hauteur)",
        OBS_FEUILLE : "Ajouter des observations sur les feuilles de mon tournesol (longueur, largeur)"
    }

    form_selector = st.selectbox("Que voulez-vous faire ?", FORM_TOURNESOL.values())

    tournesols = get_df_from_url(INSCRIPTION)

    if form_selector == FORM_TOURNESOL[INSCRIPTION]:
        st.write("## Inscrire mon tournesol :sunflower:")

        st.markdown('''
            Avant tout, vous devez inscrire votre tournesol via le formulaire ci-dessous.
            
            Votre tournesol se verra alors assigné un identifiant correspondant à votre NOMA. Vous devrez renseigner cet
            identifiant dans les autres formulaires pour rattacher vos observations à votre tournesol.
            
            :red[Si votre tournesol meurt en cours d'expérience], vous devrez inscrire votre 2ème tournesol en
            utilisant ce même formulaire et en cochant la case correspondante. Votre 2ème tournesol recevra un
            nouvel identifiant correspondant à votre NOMA + "_B", par exemple "31581300_B".
        ''')

        students = get_df_from_url('listing_etudiants')
        
        with st.form(INSCRIPTION, clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                etudiant = st.selectbox("Étudiant·e",
                                        students.agg(lambda x: f"{x['nom']} {x['prénom']} - {x['NOMA']:.0f}", axis=1),
                                        index=None,
                                        help="Si vous n'apparaîssez pas ici, contacter Antoine au plus vite.")
                second_tournesol = st.checkbox("Mon tournesol est mort. Ceci est mon 2ème tournesol.")

            with col2:
                date_reception = st.date_input("Date de réception du tournesol", format="DD/MM/YYYY",
                                               value=datetime.now(TIME_ZONE),
                                               help="Vous recevrez votre tournesol lors du TP1, en S2 ou S3 selon votre"
                                                    "groupe de TP.")

            remarque = st.text_area("Remarque :", key='remarque' + INSCRIPTION)

            if st.form_submit_button("Enregistrer"):
                mandatory_fields = [etudiant, date_reception]
                if any(field is None for field in mandatory_fields):
                    st.error(MANDATORY_FIELDS_MISSING)
                else:
                    NOMA = etudiant.split(' - ')[1]

                    if second_tournesol:
                        NOMA += "_B"

                    if tournesols.shape[0] > 0 and NOMA in tournesols['plante_ID'].astype(str).to_list():
                        st.error("Vous avez déjà inscrit votre tournesol. Si il est mort et que vous souhaitez inscrire "
                                 "un 2ème tournesol, cochez la case correspondante.")
                    else:
                        new_row = {
                            "plante_ID": str(NOMA),
                            "date_reception": date_reception.strftime("%d/%m/%Y"),
                            "remarque": remarque,
                        }

                        save_data(INSCRIPTION, new_row)

        show_data(INSCRIPTION, "tournesols")

    HELP_TEXT_ID_TOURNESOL = "L'identifiant de votre tournesol correspond à votre NOMA. Si votre 1er " \
                             "tournesol est mort, l'identifiant de votre 2nd tournesol correspond à " \
                             "votre NOMA + '_B"

    if form_selector == FORM_TOURNESOL[PIECE]:
        st.write("## Caractéristiques de ma pièce")

        st.markdown('''
            :red[Astuce] : vous pouvez taper votre NOMA dans le champ "ID du tournesol", c'est plus facile que
            de parcourir toute la liste :wink:
            
            Si votre NOMA n'apparaît, c'est que vous n'avez pas inscrit votre tournesol.
        ''')

        with st.form(PIECE, clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                plante_ID = st.selectbox("ID du tournesol *", tournesols['plante_ID'], index=None,
                                         help=HELP_TEXT_ID_TOURNESOL)
                distance_fenetre = st.number_input("Distance entre le tournesol et la fenêtre la plus proche [cm] *", step=1)
                heure_lum_art = st.number_input("Durée moyenne d'exposition à la lumière artificielle [h] *", step=0.5,
                                                min_value=0.0, max_value=18.0)
                position = st.text_input("Coordonnées GPS (extraite via clic-droit sur Google Maps) *",
                                         placeholder="50.6662847889796, 4.620254738686959")

            with col2:
                orientation = st.selectbox("Orientation de la fenêtre la plus proche *", ["Nord", "Sud", "Est", "Ouest"], index=None)
                heure_lum_nat = st.number_input("Durée moyenne d'exposition à la lumière naturelle [h] *", step=0.5,
                                                min_value=0.0, max_value=18.0)
                temp = st.selectbox("Température moyenne dans la pièce [°C] *",
                                    ["Chaude (> 21 °C)", "Moyenne (19-21 °C)", "Fraîche (17-19 °C)", "Froide (< 17 °C)"],
                                    index=None,
                                    help="Estimation de la température moyenne dans la pièce tout au long de l'expérience. "
                                         "Pour avoir une idée, mesurez quelques fois la température de la pièce entre 19 et 21h.")

            remarque = st.text_area("Remarque(s) :", key='remarque' + PIECE)

            if st.form_submit_button("Enregistrer"):
                mandatory_fields = [plante_ID, distance_fenetre, heure_lum_nat, position, orientation, heure_lum_art,
                                    temp, position]

                if any(field is None for field in mandatory_fields):
                    st.error(MANDATORY_FIELDS_MISSING)
                else:
                    new_row = {
                        "plante_ID": str(plante_ID),
                        "orientation": orientation,
                        "distance_fenetre": distance_fenetre,
                        "heure_lum_nat": heure_lum_nat,
                        "heure_lum_art": heure_lum_art,
                        "temp": temp,
                        "position": position,
                        "remarque": remarque
                    }

                    save_data(PIECE, new_row)

        show_data(PIECE, "caractéristiques des pièces")

    if form_selector == FORM_TOURNESOL[OBS_PLANTE]:
        st.write("## Observation de la plante entière")

        with st.form(OBS_PLANTE, clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                plante_ID = st.selectbox("ID du tournesol *", tournesols['plante_ID'], index=None,
                                         help=HELP_TEXT_ID_TOURNESOL)
                date_mes = st.date_input("Date de l'observation *", format="DD/MM/YYYY", value=datetime.now(TIME_ZONE))

                tournesol_mort = st.checkbox("Mon tournesol est mort cette semaine et je suis très triste 😢")

            with col2:
                stade_liste = ["A2",
                               "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12", "B13",
                               "E1", "E2", "E3"]

                hauteur = st.number_input("Hauteur (du pot jusqu'au bourgeon terminal) * [cm]", format="%.1f")
                stade = st.selectbox("Stade de la plante (voir descriptif des stades sur Moodle)", stade_liste, index=None)

            if st.form_submit_button("Enregistrer"):
                mandatory_fields = [plante_ID, date_mes, hauteur, stade]
                if any(field is None for field in mandatory_fields):
                    st.error(MANDATORY_FIELDS_MISSING)
                else:
                    new_row = {
                        "plante_ID": str(plante_ID),
                        "date": date_mes.strftime("%d/%m/%Y"),
                        "hauteur": hauteur,
                        "stade": stade,
                        "mort": tournesol_mort,
                    }

                    save_data(OBS_PLANTE, new_row)

        show_data(OBS_PLANTE, "observations de la plante entière")

    if form_selector == FORM_TOURNESOL[OBS_FEUILLE]:
        st.write("## Observation des feuilles")

        with st.form(OBS_FEUILLE, clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                plante_ID = st.selectbox("ID du tournesol *", tournesols['plante_ID'], index=None,
                                         help=HELP_TEXT_ID_TOURNESOL)
                date_mes = st.date_input("Date de l'observation *", format="DD/MM/YYYY", value=datetime.now(TIME_ZONE))

            with col2:
                rang = st.number_input("Rang de la feuille *", step=1, min_value=1,
                                       help="Numéro d'ordre de la feuille (par ordre d'apparition). La feuille la plus "
                                            "âgée (rang 1) est la feuille la plus basse alors que la feuille la plus "
                                            "récente (rang élevé) est celle qui se trouve le plus haut. Chez le tournesol, "
                                            "les premières feuilles sont parfois opposées. Dans ce cas, vous pouvez les "
                                            "numéroter 1 et 2 au hasard, puis 3 et 4 au hasard.")
                longueur = st.number_input("Longueur de la feuille * [cm]", format="%.1f",
                                           help="Se mesure de la base du limbe (contre la fin du pétiole) jusqu'à la "
                                                "pointe de la feuille.")
                largeur = st.number_input("Largeur de la feuille * [cm]", format="%.1f",
                                          help="Se mesure à l'endroit le plus large du limbe.")

            if st.form_submit_button("Enregistrer"):
                mandatory_fields = [plante_ID, date_mes, rang, longueur, largeur]
                if any(field is None for field in mandatory_fields):
                    st.error(MANDATORY_FIELDS_MISSING)
                else:
                    new_row = {
                        "plante_ID": str(plante_ID),
                        "date": date_mes.strftime("%d/%m/%Y"),
                        "rang": rang,
                        "longueur": longueur,
                        "largeur": largeur,
                    }

                    save_data(OBS_FEUILLE, new_row)

        show_data(OBS_FEUILLE, "observations des feuilles")
