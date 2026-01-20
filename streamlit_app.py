import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_confetti import confetti

# 1. Connection Setup
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Please set SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets.")
    st.stop()

st.set_page_config(page_title="Goal Tracker", layout="centered")

# 2. Login / Sign Up Logic (Username Only)
if "user" not in st.session_state:
    st.title("🎯 Resolution Tracker")
    tab_log, tab_reg = st.tabs(["Login", "Create Account"])
    
    with tab_log:
        u_log = st.text_input("Username", key="l_u")
        p_log = st.text_input("Password", type="password", key="l_p")
        if st.button("Sign In", use_container_width=True):
            # Convert Username to Dummy Email
            try:
                res = supabase.auth.sign_in_with_password({"email": f"{u_log}@app.local", "password": p_log})
                st.session_state.user = res.user
                st.rerun()
            except: st.error("Invalid username or password.")
            
    with tab_reg:
        u_reg = st.text_input("Choose Username", key="r_u")
        p_reg = st.text_input("Choose Password", type="password", key="r_p")
        if st.button("Register", use_container_width=True):
            try:
                # Register with Dummy Email
                supabase.auth.sign_up({"email": f"{u_reg}@app.local", "password": p_reg})
                st.success(f"Account '{u_reg}' created! You can now login.")
            except: st.error("Username taken or password too short.")
    st.stop()

# 3. Authenticated Content
uid = st.session_state.user.id
username = st.session_state.user.email.split('@')[0]

# --- Sidebar ---
with st.sidebar:
    st.write(f"Logged in as: **{username}**")
    if st.button("Logout"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()
    st.divider()
    st.header("New Goal")
    g_title = st.text_input("Resolution Name")
    g_mode = st.radio("Tracking", ["Binary", "Numeric"])
    g_target = st.number_input("Goal Target", value=1.0) if g_mode == "Numeric" else 1.0
    if st.button("Add Goal"):
        if g_title:
            supabase.table("resolutions").insert({
                "title": g_title, "tracking_type": g_mode, 
                "target_value": g_target, "user_id": uid
            }).execute()
            st.rerun()

# --- Dashboard ---
st.title(f"🚀 {username}'s Progress")
res = supabase.table("resolutions").select("*").execute()
df = pd.DataFrame(res.data)

if not df.empty:
    done_count = len(df[df['is_completed'] == True])
    total_count = len(df)
    st.metric("Total Completed", f"{done_count} / {total_count}")
    st.progress(done_count / total_count if total_count > 0 else 0)
    
    t_active, t_done = st.tabs(["Active", "Completed"])
    
    with t_active:
        active_df = df[df['is_completed'] == False]
        for _, r in active_df.iterrows():
            with st.expander(r['title'], expanded=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    if r['tracking_type'] == "Binary":
                        if st.button("Finish", key=f"f_{r['id']}"):
                            supabase.table("resolutions").update({"is_completed": True, "current_value": 1}).eq("id", r['id']).execute()
                            confetti()
                            st.rerun()
                    else:
                        val = st.number_input("Current", value=float(r['current_value']), key=f"v_{r['id']}")
                        if val != r['current_value']:
                            is_now_done = val >= r['target_value']
                            supabase.table("resolutions").update({"current_value": val, "is_completed": is_now_done}).eq("id", r['id']).execute()
                            if is_now_done: confetti()
                            st.rerun()
                with c2:
                    if st.button("🗑️", key=f"del_{r['id']}"):
                        supabase.table("resolutions").delete().eq("id", r['id']).execute()
                        st.rerun()

    with t_done:
        for _, r in df[df['is_completed'] == True].iterrows():
            col1, col2 = st.columns([4, 1])
            col1.success(f"**{r['title']}**")
            if col2.button("🗑️", key=f"del_c_{r['id']}"):
                supabase.table("resolutions").delete().eq("id", r['id']).execute()
                st.rerun()
else:
    st.info("No goals yet. Use the sidebar to add your first resolution!")
