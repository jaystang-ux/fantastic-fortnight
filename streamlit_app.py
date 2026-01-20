import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_confetti import confetti

# 1. Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="My Private Goals", layout="centered")

# 2. Authentication Logic
if "user" not in st.session_state:
    st.title("🔐 Goal Tracker")
    t1, t2 = st.tabs(["Login", "Create Account"])
    
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Sign In"):
            dummy = f"{u}@app.local"
            try:
                res = supabase.auth.sign_in_with_password({"email": dummy, "password": p})
                st.session_state.user = res.user
                st.rerun()
            except: st.error("Invalid credentials.")
                
    with t2:
        nu = st.text_input("Choose Username", key="r_u")
        np = st.text_input("Choose Password", type="password", key="r_p")
        if st.button("Register"):
            dummy = f"{nu}@app.local"
            try:
                supabase.auth.sign_up({"email": dummy, "password": np})
                st.success("Account created! You can now login.")
            except: st.error("Username taken.")
    st.stop()

# 3. User Identity
# This converts 'JohnDoe@app.local' back to 'JohnDoe' for the UI
user_email = st.session_state.user.email
display_name = user_email.split('@')[0]
uid = st.session_state.user.id

# 4. Main Interface
st.title(f"🎯 {display_name}'s Dashboard")

tab_main, tab_done, tab_settings = st.tabs(["🚀 Active", "✅ Finished", "⚙️ Settings"])

with tab_settings:
    st.subheader("Account Settings")
    st.info(f"Your unique ID: {uid}") # Shown for technical reference
    
    st.markdown("---")
    st.write("### Link Real Email")
    st.write(f"Current Email: **{user_email}**")
    
    new_email = st.text_input("Enter new email address")
    if st.button("Update Email"):
        try:
            # This updates the identity in Supabase Auth
            supabase.auth.update_user({"email": new_email})
            st.success("Email updated! Please logout and log back in with your new email.")
        except Exception as e:
            st.error(f"Error: {e}")

with tab_main:
    # --- Add Goal Logic ---
    with st.expander("➕ Add New Goal"):
        name = st.text_input("Title")
        mode = st.radio("Mode", ["Binary", "Numeric"])
        targ = st.number_input("Target", value=1.0) if mode == "Numeric" else 1.0
        if st.button("Save"):
            supabase.table("resolutions").insert({
                "title": name, "tracking_type": mode, "target_value": targ, "user_id": uid
            }).execute()
            st.rerun()

    # --- Fetch and Display ---
    res = supabase.table("resolutions").select("*").execute()
    df = pd.DataFrame(res.data)
    
    if not df.empty:
        active = df[df['is_completed'] == False]
        for _, r in active.iterrows():
            st.write(f"### {r['title']}")
            if st.button("Mark as Done", key=f"c_{r['id']}"):
                supabase.table("resolutions").update({"is_completed": True}).eq("id", r['id']).execute()
                confetti()
                st.rerun()

with tab_done:
    if not df.empty:
        finished = df[df['is_completed'] == True]
        for _, r in finished.iterrows():
            st.success(f"Completed: {r['title']}")

# Sidebar Logout
st.sidebar.button("Logout", on_click=lambda: (supabase.auth.sign_out(), st.session_state.clear()))
