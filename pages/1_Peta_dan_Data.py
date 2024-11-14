import streamlit as st
import os
import json

import pandas as pd
import folium
from streamlit_folium import st_folium

from streamlit_gsheets import GSheetsConnection

# Caching data load for performance
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="data")
    df["Bulan Panen"] = df["Bulan Panen"].apply(lambda x: eval(x) if isinstance(x, str) else [])
    return df

# Define months for display
months = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei",
    6: "Juni", 7: "Juli", 8: "Agustus", 9: "September",
    10: "Oktober", 11: "November", 12: "Desember"
}

# st.sidebar.button("Logout", on_click=logout, key="logout_button")
st.title("Peta Sebaran SDA di Pulau Sulawesi")
data = load_data()
if st.button("Refresh Data..."):
    st.cache_data.clear()
    data = load_data()

# Sidebar filter reset functionality - Single Reset Filters button
if "reset_filters" not in st.session_state:
    st.session_state["reset_filters"] = False

# Reset Filters Button functionality
if st.sidebar.button("Reset Filters", key="reset_button"):
    # Clear all filter selections and reset available options
    st.session_state["selected_months"] = []
    st.session_state["selected_commodities"] = []
    st.session_state["selected_provinces"] = []
    st.session_state["selected_kota_kabupaten"] = []

    # Reset the available options based on the unfiltered data
    st.session_state["available_months"] = sorted(set(sum(data["Bulan Panen"], [])))
    st.session_state["available_commodities"] = data["Komoditas"].unique()
    st.session_state["available_provinces"] = data["Provinsi"].unique()
    st.session_state["available_kota_kabupaten"] = data["Kota/Kabupaten"].unique()
    st.session_state.reset_filters = True
else:
    st.session_state.reset_filters = False

# Sidebar filters
st.sidebar.header("Opsi Filter")

# Dynamic filtering based on session state
if "selected_months" not in st.session_state:
    st.session_state["selected_months"] = []
if "selected_commodities" not in st.session_state:
    st.session_state["selected_commodities"] = []
if "selected_provinces" not in st.session_state:
    st.session_state["selected_provinces"] = []
if "selected_kota_kabupaten" not in st.session_state:
    st.session_state["selected_kota_kabupaten"] = []

# Function to apply filters and update available options
def apply_filters():
    filtered_data = data.copy()

    # Apply each filter if it has a selection
    if st.session_state["selected_months"]:
        filtered_data = filtered_data[filtered_data["Bulan Panen"].apply(lambda x: any(month in x for month in st.session_state["selected_months"]))]
    if st.session_state["selected_commodities"]:
        filtered_data = filtered_data[filtered_data["Komoditas"].isin(st.session_state["selected_commodities"])]
    if st.session_state["selected_provinces"]:
        filtered_data = filtered_data[filtered_data["Provinsi"].isin(st.session_state["selected_provinces"])]
    if st.session_state["selected_kota_kabupaten"]:
        filtered_data = filtered_data[filtered_data["Kota/Kabupaten"].isin(st.session_state["selected_kota_kabupaten"])]

    # Update available options for each filter based on the current filtered data
    st.session_state["available_months"] = sorted(set(sum(filtered_data["Bulan Panen"], [])))
    st.session_state["available_commodities"] = filtered_data["Komoditas"].unique()
    st.session_state["available_provinces"] = filtered_data["Provinsi"].unique()
    st.session_state["available_kota_kabupaten"] = filtered_data["Kota/Kabupaten"].unique()

    return filtered_data

# Apply the filters to get dynamically updated options
filtered_data = apply_filters()

# Harvest Months Filter
selected_months = st.sidebar.multiselect(
    "Pilih Bulan Panen",
    options=st.session_state.get("available_months", list(months.keys())),
    format_func=lambda x: months[x],
    default=st.session_state["selected_months"],
    key="selected_months"
)

# Commodities Filter
selected_commodities = st.sidebar.multiselect(
    "Pilih Komoditas",
    options=st.session_state.get("available_commodities", data["Komoditas"].unique()),
    default=st.session_state["selected_commodities"],
    key="selected_commodities"
)

# Provinces Filter
selected_provinces = st.sidebar.multiselect(
    "Pilih Provinsi",
    options=st.session_state.get("available_provinces", data["Provinsi"].unique()),
    default=st.session_state["selected_provinces"],
    key="selected_provinces"
)

# Kota/Kabupaten Filter
selected_kota_kabupaten = st.sidebar.multiselect(
    "Pilih Kota/Kabupaten",
    options=st.session_state.get("available_kota_kabupaten", data["Kota/Kabupaten"].unique()),
    default=st.session_state["selected_kota_kabupaten"],
    key="selected_kota_kabupaten"
)

# Legend/Information Section
st.write("### Informasi")
colors_config_path = os.path.join("config", "colors.json")
with open(colors_config_path, 'r') as f:
    Komoditas_colors = json.load(f)
    assert type(Komoditas_colors) == dict

# Display legend in two columns
col1, col2 = st.columns(2)
legend_items = list(Komoditas_colors.keys())
for idx, Komoditas in enumerate(legend_items):
    color = Komoditas_colors[Komoditas]
    Komoditas_data = data[data["Komoditas"] == Komoditas]
    if not Komoditas_data.empty:
        provinces = ", ".join([f"<span style='background-color: lightblue;'>{province}</span>" for province in Komoditas_data["Provinsi"].unique()])
        panen_months = ", ".join([f"<span style='background-color: lightgreen;'>{months[m]}</span>" for m in sorted(set(sum(Komoditas_data["Bulan Panen"], [])))])
        col = col1 if idx % 2 == 0 else col2
        col.markdown(f"<span style='color:{color}'>●</span> **{Komoditas.capitalize()}**: {len(Komoditas_data)} lokasi di provinsi: {provinces}. Bulan Panen: {panen_months}", unsafe_allow_html=True)

# Display Data Table
if st.checkbox("Tampilkan Tabel"):
    st.write("### Tabel")
    st.dataframe(
        filtered_data[["Place Name", "Kota/Kabupaten", "Provinsi", "URL", "Address", "Phone Number", "Komoditas"]],
        column_config={
            "Place Name": "Nama Tempat",
            "Address": "Lokasi",
            "Phone Number": "Nomor Telepon",
            "Komoditas": "Komoditas",
            "URL": st.column_config.LinkColumn("Google Maps Link")
        }
    )

# Download Button for Full Data
st.download_button(
    label="Download Seluruh Data",
    data=data.to_csv(index=False),
    file_name="full_data.csv",
    mime="text/csv"
)

# Display map
if not filtered_data.empty:
    m = folium.Map(
        location=[filtered_data["Latitude"].median(), filtered_data["Longitude"].median()],
        zoom_start=6,
        control_scale=True
    )
    for _, row in filtered_data.iterrows():
        color = Komoditas_colors.get(row["Komoditas"], 'black')
        url_link = f"<a href='{row['URL']}' target='_blank'>Click here for more info</a>" if pd.notnull(row['URL']) else "No URL available"
        popup_content = f"{row['Place Name']}<br>{url_link}"
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=300),
        ).add_to(m)
    st.write("### Peta")
    st_folium(m, width=700)
else:
    st.markdown("**Tidak ada lokasi yang tersedia, mohon reset atau ubah filter yang dipilih.**")
    empty_map = folium.Map(location=[-2.5489, 118.0149], zoom_start=6, control_scale=True)
    st_folium(empty_map, width=700)