import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_confetti import confetti

# 1. Connection
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Credential Error: Check Streamlit Secrets.")
    st.stop()

st.set_page_config(page_title="2026 Goals", page_icon="🎯", layout="centered")

# 2. Authentication
if "user" not in st.session_state:
    st.title("🎯 2026 Goal Tracker")
    t1, t2 = st.tabs(["Login", "Create Account"])
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Sign In", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": f"{u}@app.local", "password": p})
                st.session_state.user = res.user
                st.rerun()
            except: st.error("Login failed. Check username/password.")
    with t2:
        nu = st.text_input("Choose Username", key="r_u")
        np = st.text_input("Choose Password", type="password", key="r_p")
        if st.button("Register Account", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": f"{nu}@app.local", "password": np})
                st.success("Account created! You can now login.")
            except: st.error("Username taken or password too short.")
    st.stop()

# 3. User Identity
uid = st.session_state.user.id
display_name = st.session_state.user.email.split('@')[0]

# 4. Main Dashboard UI
st.title(f"🚀 {display_name}'s Goals")

tab_active, tab_done, tab_settings = st.tabs(["Active Goals", "Completed", "Settings"])

# --- SETTINGS TAB (Common Features) ---
with tab_settings:
    st.subheader("Account Management")
    st.text(f"Your UID: {uid}")
    
    # Change Password Feature
    with st.expander("🔐 Change Password"):
        new_pw = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            try:
                supabase.auth.update_user({"password": new_pw})
                st.success("Password updated successfully!")
            except Exception as e: st.error(f"Error: {e}")
            
    # Link Email Feature
    with st.expander("📧 Update/Link Email"):
        current_mail = st.session_state.user.email
        st.write(f"Current: {current_mail}")
        mail_input = st.text_input("New Email Address")
        if st.button("Verify & Update"):
            try:
                supabase.auth.update_user({"email": mail_input})
                st.info("Check your new email for a verification link.")
            except Exception as e: st.error(f"Error: {e}")

    if st.button("Log Out", type="primary", use_container_width=True):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()

# --- ACTIVE GOALS TAB ---
with tab_active:
    # Adding a goal (FIXED: Includes user_id)
    with st.expander("➕ Create New Goal"):
        name = st.text_input("Goal Title")
        cat = st.selectbox("Category", ["Health", "Finance", "Learning", "Personal"])
        mode = st.radio("Type", ["Binary (Done/Not Done)", "Numeric (Progress)"])
        target = st.number_input("Target Value", value=1.0) if mode == "Numeric (Progress)" else 1.0
        
        if st.button("Save Resolution"):
            if name:
                # CRITICAL FIX: user_id must be sent to pass RLS
                supabase.table("resolutions").insert({
                    "title": name, 
                    "category": cat,
                    "tracking_type": "Numeric" if mode == "Numeric (Progress)" else "Binary", 
                    "target_value": target,
                    "user_id": uid
                }).execute()
                st.rerun()

    # Display Goals
    res = supabase.table("resolutions").select("*").eq("user_id", uid).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        active_df = df[df['is_completed'] == False]
        for _, row in active_df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"### {row['title']}")
                    st.caption(f"Category: {row['category']}")
                    if row['tracking_type'] == "Numeric":
                        curr = float(row['current_value'])
                        targ = float(row['target_value'])
                        prog = min(curr / targ, 1.0)
                        st.progress(prog)
                        new_val = st.number_input(f"Update {row['title']}", value=curr, key=f"v_{row['id']}")
                        if new_val != curr:
                            is_done = new_val >= targ
                            supabase.table("resolutions").update({"current_value": new_val, "is_completed": is_done}).eq("id", row['id']).execute()
                            if is_done: confetti()
                            st.rerun()
                    else:
                        if st.button(f"Mark Complete", key=f"b_{row['id']}"):
                            supabase.table("resolutions").update({"is_completed": True, "current_value": 1}).eq("id", row['id']).execute()
                            confetti()
                            st.rerun()
                with c2:
                    # Delete with confirmation
                    if st.button("🗑️", key=f"del_{row['id']}"):
                        supabase.table("resolutions").delete().eq("id", row['id']).execute()
                        st.rerun()
    else:
        st.info("You have no active goals.")

# --- COMPLETED TAB ---
with tab_done:
    if not df.empty:
        done_df = df[df['is_completed'] == True]
        for _, row in done_df.iterrows():
            st.success(f"✅ **{row['title']}** - {row['category']}")
            if st.button("Delete History", key=f"dc_{row['id']}"):
                supabase.table("resolutions").delete().eq("id", row['id']).execute()
                st.rerun()
