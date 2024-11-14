import streamlit as st
import json
import os
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["GOOGLE_MAPS_API_KEY"] = st.secrets["GOOGLE_MAPS_API_KEY"]

import numpy as np
import pandas as pd

from streamlit_gsheets import GSheetsConnection
from utils.scraper import *

# Caching data load for performance
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet='data')
    df["Bulan Panen"] = df["Bulan Panen"].apply(lambda x: eval(x) if isinstance(x, str) else [])
    return df

colors_config_path = os.path.join("config", "colors.json")
# Loading colors configuration
def load_colors_config(colors_config_path=colors_config_path):
    with open(colors_config_path, 'r') as f:
        commodity_colors = json.load(f)
        assert type(commodity_colors) == dict

    return commodity_colors

# Function to create HTML for colored circle
def color_circle(color):
    return f'<svg width="20" height="20"><circle cx="10" cy="10" r="8" fill="{color}" /></svg>'

gsheet_data = load_data()
commodity_colors = load_colors_config()

months = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei",
    6: "Juni", 7: "Juli", 8: "Agustus", 9: "September",
    10: "Oktober", 11: "November", 12: "Desember"
}

st.title("Google Maps Scraper")
if st.button("Refresh Data..."):
    st.cache_data.clear()
    gsheet_data = load_data()
# Add a sidebar to display existing commodity-color pairs
with st.sidebar:
    st.header("Daftar Komoditas dan Warna")
    for commodity, color in commodity_colors.items():
        st.markdown(f"{color_circle(color)} {commodity}", unsafe_allow_html=True)

# Input Component 1: Text Input
search_keywords = st.text_input("Masukkan kata-kata yang ingin dicari di Google Maps...", key = "input_1")

# Input Component 2: Commodity Selection
options = list(commodity_colors.keys())
options.insert(0, "Tambah komoditas baru...")

selected_commodity_option = st.selectbox(
    "Pilih komoditas", 
    options
)

if selected_commodity_option == "Tambah komoditas baru...":
    new_commodity = st.text_input("Tulis nama komoditas baru...")
    new_color = st.color_picker("Pilih warna baru untuk komoditas baru...")
    commodity_colors[new_commodity] = new_color

    months_range = range(1,13)
    selected_months = st.multiselect(
        "Pilihlah bulan panen dari komoditas baru ini...",
        options = months,
        format_func = lambda x: f"{months[x]}"
    )
else:
    # Use st.markdown to render the HTML
    st.markdown(f"Pilihan: {selected_commodity_option} {color_circle(commodity_colors.get(selected_commodity_option, '#FFFFFF'))}", unsafe_allow_html=True)
    try:
        selected_months = gsheet_data[gsheet_data["Komoditas"] == selected_commodity_option]["Bulan Panen"].values[0]
    except:
        selected_months = st.multiselect(
            "Pilihlah bulan panen dari komoditas baru ini...",
            options = months,
            format_func = lambda x: f"{months[x]}"
        )     
    st.write(f"Komoditas yang Anda pilih: {selected_commodity_option} memiliki panen pada bulan-bulan berikut: {', '.join([months[sm] for sm in selected_months])}")

#########################################
if search_keywords:
    st.write("##### Pencarian akan dilakukan dengan konfigurasi seperti di atas. Silakan tekan tombol di bawah ini jika sudah yakin.")
    if st.button("Cari di Google Maps!"):
        with open(colors_config_path, 'w') as f:
            json.dump(commodity_colors, f, indent=4)

        if selected_commodity_option != 'Tambah komoditas baru...':
            commodity_to_search = selected_commodity_option
        else:
            commodity_to_search = new_commodity

        with st.spinner("AI sedang mencari data...Estimasi waktu 3 menit...Mohon jangan me-refresh atau menutup tab ini..."):
            df_new_commodity = search_and_save(search_string=search_keywords,
                                            commodity=commodity_to_search,
                                            bulan_panen=selected_months)
            st.toast("Melakukan update data ke Google Sheets...Mohon jangan menutup tab ini...")
            
            st.cache_data.clear()
            gsheet_data = load_data()
            
            df_update = pd.concat([gsheet_data, df_new_commodity], ignore_index=True)
            df_update = df_update.drop_duplicates(subset=['ID', 'Latitude', 'Longitude']).reset_index(drop = True)

            conn = st.connection("gsheets", type=GSheetsConnection)
            try:
                conn.update(worksheet='data', data=df_update)
            except:
                conn.create(worksheet='data', data=df_update)

            st.toast("Berhasil melakukan update data ke Google Sheets!")
        
        st.success(f"AI berhasil mencari {df_new_commodity.shape[0]} data baru.")

        st.cache_data.clear()
        gsheet_data = load_data()
        st.markdown(f"Silakan membuka Google Sheet [di sini](https://docs.google.com/spreadsheets/d/1vdggN37wqyG5hVywLaa21Xw-EFOMEvTJ9KhCG_wKRZY/edit?usp=sharing) untuk melihat keseluruhan data")
