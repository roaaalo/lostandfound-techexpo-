import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# ------------------- CONFIGURATION -------------------
TYPE_OPTIONS = ["Lost", "Found"]
CATEGORY_OPTIONS = [
    "Pets & Animals", "Electronics", "Bags & Wallets", "Jewelry",
    "Documents & Cards", "Clothing & Accessories", "Personal Items", "Other"
]
CITY_OPTIONS = [
    "Kuwait City", "Salmiya", "Hawally", "Jahra",
    "Farwaniya", "Ahmadi", "Mubarak Al-Kabeer"
]

DATA_FILE = "announcements.csv"
IMAGES_FOLDER = "announcement_images"
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# ------------------- DATA HANDLING -------------------
def load_data():
    columns = [
        "ID", "Type", "Category", "City", "Description",
        "Image1", "Image2", "Image3", "Phone",
        "Date", "EventDate", "DeletePassword", "Resolved"
    ]
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str)
        for c in columns:
            if c not in df.columns:
                df[c] = ""
        df["Resolved"] = df["Resolved"].fillna("False").astype(str).str.lower().map({
            "true": True, "false": False, "1": True, "0": False
        }).fillna(False).astype(bool)
        return df[columns]
    else:
        return pd.DataFrame(columns=columns)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def save_images(files):
    paths = []
    for file in files[:3]:
        if file is not None:
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}_{file.name}"
            filepath = os.path.join(IMAGES_FOLDER, filename)
            with open(filepath, "wb") as f:
                f.write(file.getbuffer())
            paths.append(filepath)
    while len(paths) < 3:
        paths.append("")
    return paths

# ------------------- LOAD DATA -------------------
df = load_data()

# ------------------- SESSION STATE -------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# ------------------- HOME PAGE -------------------
def home_page():
    st.title("🧭 Lost & Found in Kuwait")
    st.write("Find what you’ve lost or help others recover what they’ve misplaced.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Search for an Item", use_container_width=True):
            st.session_state.page = "search"
    with col2:
        if st.button("📦 Report an Item", use_container_width=True):
            st.session_state.page = "report"

# ------------------- REPORT PAGE -------------------
def report_page():
    global df  # declare global at the start
    st.header("📦 Report a Lost or Found Item")
    f1, f2, f3 = st.columns(3)
    with f1:
        post_type = st.radio("Type", TYPE_OPTIONS, horizontal=True)
    with f2:
        category = st.selectbox("Category", CATEGORY_OPTIONS)
    with f3:
        city = st.selectbox("City / Area", CITY_OPTIONS)

    description = st.text_area("📝 Description of the item")
    event_date = st.date_input(f"📅 Date the item was {post_type.lower()}")
    phone = st.text_input("📞 Contact Phone Number (8 digits)")
    delete_password = st.text_input("🔒 Set a delete password for this post", type="password")
    uploaded_files = st.file_uploader(
        "🖼️ Upload up to 3 pictures", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )

    if st.button("✅ Submit Announcement", use_container_width=True):
        if not description:
            st.error("Please enter a description.")
        elif len(phone) != 8 or not phone.isdigit():
            st.error("Phone number must be exactly 8 digits.")
        elif not delete_password:
            st.error("Please set a delete password.")
        else:
            image_paths = save_images(uploaded_files)
            new_id = str(len(df) + 1)
            new_post = {
                "ID": new_id,
                "Type": post_type.lower(),
                "Category": category,
                "City": city,
                "Description": description,
                "Image1": image_paths[0],
                "Image2": image_paths[1],
                "Image3": image_paths[2],
                "Phone": phone,
                "Date": datetime.today().strftime("%Y-%m-%d"),
                "EventDate": event_date.strftime("%Y-%m-%d"),
                "DeletePassword": delete_password.strip(),
                "Resolved": False,
            }
            df.loc[len(df)] = new_post
            save_data(df)
            st.success("✅ Announcement posted successfully!")
            st.session_state.page = "home"

    if st.button("⬅️ Back to Home", use_container_width=True):
        st.session_state.page = "home"

# ------------------- SEARCH PAGE -------------------
def search_page():
    global df  # declare global at the start
    st.header("📢 Lost & Found Announcements")
    st.write("Browse and filter through all posted announcements below.")

    # Search & filters
    search_query = st.text_input("Search by keyword (e.g., 'wallet', 'dog', 'bag')", key="search_query")

    st.markdown("### Filters")
    colA, colB, colC = st.columns(3)
    with colA:
        filter_type = st.selectbox("Type", ["All"] + TYPE_OPTIONS)
    with colB:
        filter_category = st.selectbox("Category", ["All"] + CATEGORY_OPTIONS)
    with colC:
        filter_city = st.selectbox("City / Area", ["All"] + CITY_OPTIONS)

    dcol1, dcol2 = st.columns(2)
    with dcol1:
        start_date = st.date_input("From Date", datetime(2024, 1, 1))
    with dcol2:
        end_date = st.date_input("To Date", datetime.today())

    st.markdown("---")

    # Apply filters
    filtered = df.copy()
    if filter_type != "All":
        filtered = filtered[filtered["Type"] == filter_type.lower()]
    if filter_category != "All":
        filtered = filtered[filtered["Category"] == filter_category]
    if filter_city != "All":
        filtered = filtered[filtered["City"] == filter_city]
    if search_query:
        filtered = filtered[filtered["Description"].str.contains(search_query, case=False, na=False)]

    # Date filter
    if not filtered.empty:
        filtered["EventDate"] = pd.to_datetime(filtered["EventDate"], errors="coerce")
        mask = (filtered["EventDate"] >= pd.to_datetime(start_date)) & (filtered["EventDate"] <= pd.to_datetime(end_date))
        filtered = filtered[mask]

    # Display announcements
    if filtered.empty:
        st.info("No announcements match your filters.")
    else:
        filtered = filtered.sort_values("Date", ascending=False)
        for idx, row in filtered.iterrows():
            st.markdown("---")
            indicator = "🔴 Lost" if row["Type"] == "lost" else "🟢 Found"
            st.subheader(f"{indicator} — {row['Category']}")
            st.caption(f"{row['City']} • Event: {row['EventDate'].strftime('%Y-%m-%d')} • Posted: {row['Date']}")

            # Images
            images = [row["Image1"], row["Image2"], row["Image3"]]
            images = [img for img in images if img and os.path.exists(img)]
            if images:
                img_cols = st.columns(len(images))
                for j, img_path in enumerate(images):
                    with img_cols[j]:
                        st.image(img_path, use_container_width=True)

            st.write(f"**Description:** {row['Description']}")
            st.write(f"**📞 Contact:** {row['Phone']}")

            # Delete functionality
            entered_password = st.text_input(
                "Enter delete password", type="password", key=f"del_{row['ID']}"
            )
            if st.button("🗑️ Delete Announcement", key=f"del_btn_{row['ID']}"):
                if entered_password == row["DeletePassword"]:
                    df.drop(df[df["ID"] == row["ID"]].index, inplace=True)
                    save_data(df)
                    st.success("✅ Announcement deleted successfully!")
                    return  # exit function to refresh display
                else:
                    st.error("❌ Incorrect password. Cannot delete this announcement.")

    if st.button("⬅️ Back to Home", use_container_width=True):
        st.session_state.page = "home"

# ------------------- PAGE ROUTING -------------------
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "report":
    report_page()
elif st.session_state.page == "search":
    search_page()
