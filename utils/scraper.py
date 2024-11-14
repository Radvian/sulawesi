import requests
import time
import pandas as pd

from pydantic import BaseModel
from openai import OpenAI
from typing import List, Optional

import streamlit as st
import os
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["GOOGLE_MAPS_API_KEY"] = st.secrets["GOOGLE_MAPS_API_KEY"]


def search_places(search_query, max_pages=50):
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': os.environ["GOOGLE_MAPS_API_KEY"],  # Replace with your actual API key
        'X-Goog-FieldMask': 'places.id,places.displayName,places.location,places.formattedAddress,places.internationalPhoneNumber,places.googleMapsUri,nextPageToken'
    }
    # Define the initial request payload
    payload = {
        "textQuery": search_query,
        "locationRestriction": {
            "rectangle": {
                "low": {
                    "latitude": -6.595252,
                    "longitude": 118.215282
                },
                "high": {
                    "latitude": 2.217835,
                    "longitude": 125.360649
                }
            }
        },
        "pageSize": 20  # Number of results per page
    }
    
    page_count = 0
    all_places = []

    while page_count < max_pages:
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check for a successful request
        if response.status_code == 200:
            places_data = response.json().get('places', [])
            if not places_data:
                print("No more results.")
                break
            
            # Append each place's details to the all_places list
            for place in places_data:
                place_details = {
                    "id": place.get('id', 'N/A'),
                    "name": place.get('displayName', {}).get('text', 'Unknown'),
                    "latitude": place.get('location', {}).get('latitude', 'N/A'),
                    "longitude": place.get('location', {}).get('longitude', 'N/A'),
                    "address": place.get('formattedAddress', 'No address available'),
                    "phone_number": place.get('internationalPhoneNumber', ''),
                    "google_maps_link": place.get('googleMapsUri', 'No Google Maps link available')
                }
                all_places.append(place_details)

            # Check for nextPageToken
            next_page_token = response.json().get('nextPageToken')
            if next_page_token:
                payload['pageToken'] = next_page_token
                page_count += 1
                time.sleep(2)  # Delay to let the nextPageToken become active
            else:
                break
        else:
            print("Error:", response.status_code, response.json())
            break

    return all_places  # Return a list of all places gathered

def parse_address(address_string):
    client = OpenAI()

    class Address(BaseModel):
        dusun: Optional[str] = None
        kecamatan: Optional[str] = None
        kota_kabupaten: Optional[str] = None
        provinsi: Optional[str] = None
        kode_pos: Optional[int] = None

    completion = client.beta.chat.completions.parse(
        model = 'gpt-4o-mini',
        messages = [
            {'role':'system', 'content': "You are a master of the Indonesian Geeography and maps. Please parse the input string into dusun, kecamatan, kota/kabupaten, provinsi, and kode pos. Not all fields should be filled if the data is not available. Start each kota/kabupaten with Kota or Kabupaten then the name. For province name, parse it in Bahasa Indonesia. Remember that Gorontalo can be a city and a province name too. Think critically."},
            {'role':'user', 'content':f"{address_string}"}
        ],
        response_format = Address
    )
    address_parsed = completion.choices[0].message.parsed

    return address_parsed

def search_and_save(search_string:str, commodity:str, bulan_panen:list):
    try:
        st.toast("Sedang mencari di Google Maps...", icon='🚀')
        search_result = search_places(search_string)
        st.success("Berhasil memperoleh data dari Google Maps! Sedang membersihkan data...")

        st.toast("Membersihkan data yang diperoleh...", icon='🚀')
        for s in search_result: 
            try:
                parsed_addr = parse_address(s["address"])
                s["dusun"] = parsed_addr.dusun
                s["kecamatan"] = parsed_addr.kecamatan
                s["kota_kabupaten"] = parsed_addr.kota_kabupaten
                s["provinsi"] = parsed_addr.provinsi
                s["kode_pos"] = parsed_addr.kode_pos
                s["komoditas"] = commodity
                s["bulan_panen"] = bulan_panen
            except:
                search_result.remove(s)
                pass

        data = search_result
        transposed_data = {key: [d[key] for d in data] for key in data[0]}
        df = pd.DataFrame(transposed_data)
        df.columns = ['ID', 'Place Name', 'Latitude', 'Longitude', 'Address', 'Phone Number', 'URL', 'Dusun', 'Kecamatan', 'Kota/Kabupaten', 'Provinsi', 'Kode Pos', 'Komoditas', 'Bulan Panen']
        df['Phone Number'] = df['Phone Number'].apply(lambda x: f" {x}" if pd.notnull(x) and x != "" else "")
        st.success("Berhasil membersihkan data dari Google Maps! Melakukan update data ke Google Sheets...")
        return df

    except Exception as e:
        print(s)
        raise