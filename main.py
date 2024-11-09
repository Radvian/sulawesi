import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Initialize session state for login status
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Login form if not authenticated
if not st.session_state["authenticated"]:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
            st.session_state["authenticated"] = True
            st.success("Login successful!")
        else:
            st.error("Incorrect username or password.")

# Main app content for authenticated users
if st.session_state["authenticated"]:
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        
    # Load the data
    data = pd.read_csv('scraped_data.csv')
    
    # Sidebar filters
    st.sidebar.header("Filter Options")
    kecamatan_filter = st.sidebar.multiselect("Select Kecamatan", options=data["Kecamatan"].unique())
    kota_filter = st.sidebar.multiselect("Select Kota", options=data["Kota"].unique())
    kabupaten_filter = st.sidebar.multiselect("Select Kabupaten", options=data["Kabupaten"].unique())
    provinsi_filter = st.sidebar.multiselect("Select Provinsi", options=data["Provinsi"].unique())
    type_filter = st.sidebar.multiselect("Select Type", options=data["Type"].unique())
    
    # Apply filters to data
    filtered_data = data
    if kecamatan_filter:
        filtered_data = filtered_data[filtered_data["Kecamatan"].isin(kecamatan_filter)]
    if kota_filter:
        filtered_data = filtered_data[filtered_data["Kota"].isin(kota_filter)]
    if kabupaten_filter:
        filtered_data = filtered_data[filtered_data["Kabupaten"].isin(kabupaten_filter)]
    if provinsi_filter:
        filtered_data = filtered_data[filtered_data["Provinsi"].isin(provinsi_filter)]
    if type_filter:
        filtered_data = filtered_data[filtered_data["Type"].isin(type_filter)]
    
    # Display filtered data in a table
    st.write("### Peta Kebun/Lokasi Sumber Daya Alam di Sulawesi")
    st.dataframe(filtered_data)
    
    # Initialize Folium map
    m = folium.Map(
        location=[filtered_data["Latitude"].median(), filtered_data["Longitude"].median()],
        zoom_start=6,
        control_scale=True
    )
    
    # Define colors for each unique type
    type_colors = {
        'cengkeh':'red', 
        'kakao':'blue', 
        'kebun pala':'green',
        'kebun sawit':'lightgreen', 
        'kelapa':'gold', 
        'kopi':'brown', 
        'nikel':'grey'
        # Add more types and their colors as needed
    }
    
    # Add points to the map
    for _, row in filtered_data.iterrows():
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=10,
            color=type_colors.get(row["Type"], 'gray'),
            fill=True,
            fill_color=type_colors.get(row["Type"], 'gray'),
            fill_opacity=0.7,
            popup=f"{row['Title']}, {row['Place Name']}",
        ).add_to(m)
    
    # Display map in Streamlit
    st.write("### Location Map")
    st_folium(m, width=700)
