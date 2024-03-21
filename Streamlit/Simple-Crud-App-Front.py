#run with: streamlit run front.py
import requests
import streamlit as st

# Base URL for FastAPI backend
BASE_URL = "http://localhost:8000"

st.title("CRUD Application with Streamlit")

# Function to fetch items from the backend
def fetch_items():
    response = requests.get(f"{BASE_URL}/items")
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch items")

# Create Operation
st.subheader("Add Item")
create_name = st.text_input("Name", key="create_name")
create_description = st.text_area("Description", key="create_description")
if st.button("Add"):
    response = requests.post(
        f"{BASE_URL}/items/", json={"name": create_name, "description": create_description}
    )
    if response.status_code == 200:
        st.success("Item added successfully")

# Read Operation
st.subheader("View Items")
items = fetch_items()
if items:
    for item in items:
        item_id = item['_id']
        edit_mode_key = f"edit_mode_{item_id}"
        edit_mode = st.session_state.get(edit_mode_key, False)
        if not edit_mode:
            st.write(f"Name: {item['name']}, Description: {item['description']}")
            if st.button(f"Edit {item_id}"):
                st.session_state[edit_mode_key] = True
        else:
            edit_name = st.text_input("Name", value=item['name'], key=f"edit_name_{item_id}")
            edit_description = st.text_area("Description", value=item['description'], key=f"edit_description_{item_id}")
            if st.button(f"Update {item_id}"):
                response = requests.put(
                    f"{BASE_URL}/items/{item_id}",
                    json={"name": edit_name, "description": edit_description}
                )
                if response.status_code == 200:
                    st.success("Item updated successfully")
                    st.session_state[edit_mode_key] = False
