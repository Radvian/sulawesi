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
        home = st.Page("Home.py", title="Home", default=True)
        page1 = st.Page("pages/1_Peta_dan_Data.py", title="Peta dan Data")
        page2 = st.Page("pages/2_Google_Maps_Scraper.py", title="Google Maps Scraper")

        pg = st.navigation([home, page1, page2])

        if pg == home:
            st.write("# Welcome to the main page!")
            st.write("You can now access the other pages using the sidebar navigation.")

        # Sidebar with logout button
        with st.sidebar:
            if st.button("Logout"):
                logout()

        # Run the current page
        pg.run()

if __name__ == "__main__":
    main()