import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Initialize session state for login status and other interactive states
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Function to handle login
def login(username, password):
    if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
        st.session_state["authenticated"] = True
        st.success("Login successful!")
    else:
        st.error("Incorrect username or password.")

# Function to handle logout
def logout():
    st.session_state["authenticated"] = False

# Login form if not authenticated
if not st.session_state["authenticated"]:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login", key="login_button"):
        login(username, password)

# Main app content for authenticated users
if st.session_state["authenticated"]:
    st.sidebar.button("Logout", on_click=logout, key="logout_button")

    # Sidebar filter reset functionality - Single Reset Filters button
    if "reset_filters" not in st.session_state:
        st.session_state["reset_filters"] = False

    if st.sidebar.button("Reset Filters", key="reset_button"):
        st.session_state.reset_filters = True
    else:
        st.session_state.reset_filters = False

    # Caching data load for performance
    @st.cache_data
    def load_data():
        data = pd.read_csv('sulawesi_sda_data_nov2024.csv')
        data["Panen Months"] = data["Panen Months "].apply(lambda x: eval(x) if isinstance(x, str) else [])
        return data

    st.title("Peta Sebaran SDA di Pulau Sulawesi")
    # Load the data
    data = load_data()
    
    # Define months for display
    months = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei",
        6: "Juni", 7: "Juli", 8: "Agustus", 9: "September",
        10: "Oktober", 11: "November", 12: "Desember"
    }
    
    # Sidebar filters
    st.sidebar.header("Opsi Filter")
    
    # Set default filter selections
    default_months = list(months.keys())
    default_commodities = data["Commodity"].unique()
    default_provinces = data["Provinsi"].unique()
    default_kota_kabupaten = []
    
    # Use session state to handle reset functionality
    selected_months = st.sidebar.multiselect(
        "Pilih Bulan Panen",
        options=list(months.keys()),
        format_func=lambda x: months[x],
        default=default_months if st.session_state.reset_filters else None,
        key="bulan_panen"
    )
    
    # Filter commodities based on selected months
    filtered_data = data
    if selected_months:
        filtered_data = data[data["Panen Months"].apply(lambda x: any(month in x for month in selected_months))]
    commodity_options = filtered_data["Commodity"].unique()
    
    selected_commodity = st.sidebar.multiselect(
        "Pilih Komoditas",
        options=commodity_options,
        default=commodity_options if st.session_state.reset_filters else None,
        key="commodity"
    )
    
    # Apply commodity filter to the data
    if selected_commodity:
        filtered_data = filtered_data[filtered_data["Commodity"].isin(selected_commodity)]
    
    # Filter province options based on selected commodities
    province_options = filtered_data["Provinsi"].unique()
    selected_province = st.sidebar.multiselect(
        "Pilih Provinsi",
        options=province_options,
        default=province_options if st.session_state.reset_filters else None,
        key="province"
    )
    
    # Apply province filter to the data
    if selected_province:
        filtered_data = filtered_data[filtered_data["Provinsi"].isin(selected_province)]
    
    # Filter Kota/Kabupaten options based on both selected commodity and province
    kota_kabupaten_options = filtered_data["Kota/Kabupaten"].unique()
    
    selected_kota_kabupaten = st.sidebar.multiselect(
        "Pilih Kota/Kabupaten",
        options=kota_kabupaten_options,
        default=default_kota_kabupaten if st.session_state.reset_filters else [],
        help="Select regions as per the chosen commodity and province.",
        key="kota_kabupaten"
    )
    
    # Apply Kota/Kabupaten filter to the data
    if selected_kota_kabupaten:
        filtered_data = filtered_data[filtered_data["Kota/Kabupaten"].isin(selected_kota_kabupaten)]
    
    # Check if filtered data has valid Latitude and Longitude values to avoid NaN issues
    filtered_data = filtered_data.dropna(subset=["Latitude", "Longitude"])
    
    # Legend/Information Section
    st.write("### Legend / Information")
    commodity_colors = {
        'cengkeh': '#FF0000',      # Red
        'kakao': '#0000FF',        # Blue
        'kebun pala': '#008000',   # Green
        'kelapa sawit': '#00FF00', # Light green
        'kelapa': '#FFD700',       # Gold
        'kopi': '#8B4513',         # Saddle brown
        'nikel': '#A9A9A9'         # Dark gray
    }
    
    # Create two columns for the legend display
    col1, col2 = st.columns(2)
    legend_items = list(commodity_colors.keys())
    
    # Distribute items in two columns
    for idx, commodity in enumerate(legend_items):
        color = commodity_colors[commodity]
        commodity_data = data[data["Commodity"] == commodity]
        
        if not commodity_data.empty:
            num_locations = len(commodity_data)
            
            # Highlight provinces and harvest months
            provinces = ", ".join(
                [f"<span style='background-color: lightblue;'>{province}</span>" for province in commodity_data["Provinsi"].unique()]
            )
            
            panen_months = ", ".join(
                [f"<span style='background-color: lightgreen;'>{months[m]}</span>" for m in sorted(set(sum(commodity_data["Panen Months"], [])))]
            )
            
            # Display in two columns by alternating between col1 and col2
            col = col1 if idx % 2 == 0 else col2
            col.markdown(
                f"<span style='color:{color}'>●</span> **{commodity.capitalize()}**: "
                f"{num_locations} lokasi di provinsi: {provinces}. Bulan Panen: {panen_months}",
                unsafe_allow_html=True
            )
    
    # Toggleable DataFrame Section
    if st.checkbox("Tampilkan Tabel"):
        st.write("### Tabel")
        st.dataframe(filtered_data[["Place Name", "Kota/Kabupaten", "Provinsi", "URL", "Location", "Phone Number", "Commodity"]], column_config={"Place Name":"Nama Tempat", "Location":"Lokasi", "Phone Number":"Nomor Telepon", "Commodity":"Komoditas", "URL":st.column_config.LinkColumn("Google Maps Link")})
    
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
            # Use the color from the commodity_colors dictionary
            color = commodity_colors.get(row["Commodity"], 'black')
            
            # Create a clickable URL link if URL is present
            url_link = f"<a href='{row['URL']}' target='_blank'>Click here for more info</a>" if pd.notnull(row['URL']) else "No URL available"
            
            # Create the popup content
            popup_content = f"{row['Title']}, {row['Place Name']}<br>{url_link}"
    
            # Add CircleMarker with clickable URL in popup
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
