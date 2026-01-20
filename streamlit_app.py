import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_confetti import confetti

# 1. Secure Connection
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Credential Error: Please check your Streamlit Secrets.")
    st.stop()

st.set_page_config(page_title="Goal Tracker", page_icon="🎯", layout="centered")

# 2. Authentication Logic
if "user" not in st.session_state:
    st.title("Goal Tracker")
    t1, t2 = st.tabs(["Login", "Create Account"])
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Sign In", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": f"{u}@app.local", "password": p})
                st.session_state.user = res.user
                st.rerun()
            except: st.error("Login failed. Check credentials.")
    with t2:
        nu = st.text_input("Choose Username", key="r_u")
        np = st.text_input("Choose Password", type="password", key="r_p")
        if st.button("Register Account", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": f"{nu}@app.local", "password": np})
                st.success("Account created successfully.")
            except: st.error("Registration error.")
    st.stop()

# 3. User Context
uid = st.session_state.user.id
display_name = st.session_state.user.email.split('@')[0]

# 4. Main Interface
st.header(f"Account: {display_name}")

# Using built-in Streamlit icons for tabs
tab_active, tab_done, tab_settings = st.tabs([
    "Active Goals", 
    "Completed", 
    "Settings"
])

with tab_settings:
    st.subheader("Configuration")
    if st.button("Logout", type="primary"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()

with tab_active:
    # --- ADD GOAL FORM ---
    with st.expander("Create New Goal"):
        name = st.text_input("Goal Title")
        cat = st.selectbox("Category", ["Health", "Finance", "Learning", "Personal"])
        mode = st.radio("Type", ["Binary", "Numeric"])
        target = st.number_input("Target", value=1.0) if mode == "Numeric" else 1.0
        
        if st.button("Save Resolution"):
            if name:
                supabase.table("resolutions").insert({
                    "title": name, 
                    "category": cat,
                    "tracking_type": mode, 
                    "target_value": target,
                    "user_id": uid,
                    "current_value": 0,
                    "is_completed": False
                }).execute()
                st.rerun()

    # --- DISPLAY ACTIVE GOALS ---
    res = supabase.table("resolutions").select("*").eq("user_id", uid).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        active_df = df[df['is_completed'] == False]
        for _, row in active_df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{row['title']}**")
                    if row['tracking_type'] == "Binary":
                        if st.button("Complete", key=f"done_{row['id']}"):
                            supabase.table("resolutions").update({"is_completed": True, "current_value": 1}).eq("id", row['id']).execute()
                            confetti(emojis=["✨"])
                            st.rerun()
                    else:
                        curr = float(row['current_value'])
                        targ = float(row['target_value'])
                        new_val = st.number_input(f"Progress: {row['title']}", value=curr, key=f"v_{row['id']}")
                        if new_val != curr:
                            is_done = new_val >= targ
                            supabase.table("resolutions").update({"current_value": new_val, "is_completed": is_done}).eq("id", row['id']).execute()
                            if is_done: confetti(emojis=["✨"])
                            st.rerun()
                with c2:
                    # Using '🗑️' as standard icon for delete
                    if st.button("Delete", key=f"del_{row['id']}"):
                        supabase.table("resolutions").delete().eq("id", row['id']).execute()
                        st.rerun()
    else:
        st.info("No active records.")

with tab_done:
    if not df.empty:
        done_df = df[df['is_completed'] == True]
        for _, row in done_df.iterrows():
            st.info(f"Done: {row['title']}")
            if st.button("Remove History", key=f"d_done_{row['id']}"):
                supabase.table("resolutions").delete().eq("id", row['id']).execute()
                st.rerun()
