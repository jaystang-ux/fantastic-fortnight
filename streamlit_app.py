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
    st.error("Check Streamlit Secrets.")
    st.stop()

st.set_page_config(page_title="My 2026 Goals", layout="centered")

# 2. Authentication Logic
if "user" not in st.session_state:
    st.title("🔐 My Goal Tracker")
    t1, t2 = st.tabs(["Login", "Sign Up"])
    with t1:
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Enter"):
            try:
                res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                st.session_state.user = res.user
                st.rerun()
            except: st.error("Login failed.")
    with t2:
        ne = st.text_input("New Email")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            supabase.auth.sign_up({"email": ne, "password": np})
            st.info("Check your email (or Supabase dashboard) to confirm.")
    st.stop()

# 3. App Content (User Logged In)
uid = st.session_state.user.id

def fetch_data():
    res = supabase.table("resolutions").select("*").execute()
    return pd.DataFrame(res.data)

# Sidebar UI
with st.sidebar:
    st.write(f"User: {st.session_state.user.email}")
    if st.button("Logout"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()
    st.divider()
    st.header("Add Goal")
    name = st.text_input("Title")
    cat = st.selectbox("Cat", ["Health", "Finance", "Skill", "Other"])
    mode = st.radio("Mode", ["Binary", "Numeric"])
    targ = st.number_input("Target", value=1.0) if mode == "Numeric" else 1.0
    if st.button("Save"):
        supabase.table("resolutions").insert({
            "title": name, "category": cat, "tracking_type": mode, 
            "target_value": targ, "user_id": uid
        }).execute()
        st.rerun()

# Dashboard UI
df = fetch_data()
if not df.empty:
    done = len(df[df['is_completed'] == True])
    total = len(df)
    st.metric("Progress", f"{done} / {total}")
    st.progress(done/total)
    
    act, comp = st.tabs(["🚀 Active", "✅ Finished"])
    
    with act:
        for _, r in df[df['is_completed'] == False].iterrows():
            with st.expander(r['title']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    if r['tracking_type'] == "Binary":
                        if st.button("Done", key=f"d_{r['id']}"):
                            supabase.table("resolutions").update({"current_value": 1, "is_completed": True}).eq("id", r['id']).execute()
                            confetti()
                            st.rerun()
                    else:
                        v = st.number_input("Val", value=float(r['current_value']), key=f"v_{r['id']}")
                        if v >= r['target_value']:
                            supabase.table("resolutions").update({"current_value": v, "is_completed": True}).eq("id", r['id']).execute()
                            confetti()
                            st.rerun()
                with c2:
                    if st.button("🗑️", key=f"del_{r['id']}"):
                        supabase.table("resolutions").delete().eq("id", r['id']).execute()
                        st.rerun()

    with comp:
        for _, r in df[df['is_completed'] == True].iterrows():
            st.success(r['title'])
            if st.button("Delete", key=f"del_c_{r['id']}"):
                supabase.table("resolutions").delete().eq("id", r['id']).execute()
                st.rerun()
else:
    st.info("Start by adding a goal.")
