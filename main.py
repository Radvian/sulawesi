import streamlit as st
from streamlit.runtime.state import SessionStateProxy
import os
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["GOOGLE_MAPS_API_KEY"] = st.secrets["GOOGLE_MAPS_API_KEY"]

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login(username, password):
    if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
        st.session_state.logged_in = True
        st.success("Login successful!")
        return True
    else:
        st.error("Incorrect username or password.")
        return False

def logout():
    st.session_state.logged_in = False
    st.rerun()

def main():
    if not st.session_state.logged_in:
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    else:
        # Navigation setup
        home = st.Page("main.py", title="Home", default=True)
        page1 = st.Page("pages/1_peta_dan_data.py", title="Peta dan Data")
        page2 = st.Page("pages/2_google_maps_scraper.py", title="Google Maps Scraper")

        pg = st.navigation([home, page1, page2])

        if pg == home:
            st.write("# Selamat Datang di Halaman Utama")
            st.markdown("""
            #### 1. Halaman "Peta dan Data" memiliki peta yang dapat difilter untuk menunjukan pesebaran sumber daya alam (SDA) di Sulawesi, beserta dengan link ke Google Maps.
            #### 2. Halaman "Google Maps Scraper" memampukan kita untuk melakukan web-scraping (ekstraksi data dari internet) yang dibantu oleh AI supaya mempermudah kita dalam pengumpulan data.
            
            #### Data dalam bentuk Google Spreadsheet terdapat di [link ini](https://docs.google.com/spreadsheets/d/1vdggN37wqyG5hVywLaa21Xw-EFOMEvTJ9KhCG_wKRZY/edit?gid=1381996917#gid=1381996917)"""

        # Sidebar with logout button
        with st.sidebar:
            if st.button("Logout"):
                logout()

        # Run the current page
        pg.run()

if __name__ == "__main__":
    main()
