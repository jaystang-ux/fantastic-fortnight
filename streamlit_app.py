import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_confetti import confetti

# 1. Connection Initialization
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Credential Error: Verify Streamlit Secrets.")
    st.stop()

st.set_page_config(page_title="Goal Tracker", layout="centered")

# 2. Authentication (Username Logic)
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
            except: st.error("Login failed.")
    with t2:
        nu = st.text_input("Choose Username", key="r_u")
        np = st.text_input("Choose Password", type="password", key="r_p")
        if st.button("Register Account", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": f"{nu}@app.local", "password": np})
                st.success("Account created. You may now login.")
            except: st.error("Registration failed.")
    st.stop()

# 3. Session Context
uid = st.session_state.user.id
email_current = st.session_state.user.email
display_name = email_current.split('@')[0]

# 4. Data Fetching (Scoped to User)
def fetch_user_data():
    res = supabase.table("resolutions").select("*").eq("user_id", uid).execute()
    return pd.DataFrame(res.data)

df = fetch_user_data()

# 5. Dashboard
st.header(f"System: {display_name}")
tab_active, tab_done, tab_settings = st.tabs(["Active Goals", "Completed", "Settings"])

# --- TAB: ACTIVE GOALS ---
with tab_active:
    with st.expander("Add New Resolution"):
        name = st.text_input("Title")
        cat = st.selectbox("Category", ["Health", "Finance", "Learning", "Personal"])
        mode = st.radio("Tracking Method", ["Binary", "Numeric"])
        target = st.number_input("Target", value=1.0) if mode == "Numeric" else 1.0
        
        if st.button("Save Entry"):
            if name:
                # Included 'user_id' to resolve APIError 42501
                supabase.table("resolutions").insert({
                    "title": name, "category": cat, "tracking_type": mode, 
                    "target_value": target, "user_id": uid, "current_value": 0
                }).execute()
                st.rerun()

    if not df.empty:
        active_items = df[df['is_completed'] == False]
        for _, r in active_items.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"**{r['title']}** | {r['category']}")
                    if r['tracking_type'] == "Numeric":
                        curr = float(r['current_value'])
                        targ = float(r['target_value'])
                        st.progress(min(curr/targ, 1.0))
                        new_val = st.number_input(f"Update: {r['title']}", value=curr, key=f"val_{r['id']}")
                        if new_val != curr:
                            done = new_val >= targ
                            supabase.table("resolutions").update({"current_value": new_val, "is_completed": done}).eq("id", r['id']).execute()
                            if done: confetti(emojis=["✨"])
                            st.rerun()
                    else:
                        if st.button("Mark Complete", key=f"fin_{r['id']}"):
                            supabase.table("resolutions").update({"is_completed": True, "current_value": 1}).eq("id", r['id']).execute()
                            confetti(emojis=["✨"])
                            st.rerun()
                with c2:
                    if st.button("Delete", key=f"del_{r['id']}"):
                        supabase.table("resolutions").delete().eq("id", r['id']).execute()
                        st.rerun()

# --- TAB: COMPLETED ---
with tab_done:
    if not df.empty:
        done_items = df[df['is_completed'] == True]
        st.metric("Total Successes", len(done_items))
        for _, r in done_items.iterrows():
            st.info(f"Verified: {r['title']}")
            if st.button("Remove Record", key=f"rem_{r['id']}"):
                supabase.table("resolutions").delete().eq("id", r['id']).execute()
                st.rerun()

# --- TAB: SETTINGS (RESTORED FEATURES) ---
with tab_settings:
    st.subheader("Account Management")
    
    # Update Password
    with st.expander("Update Password"):
        up_pw = st.text_input("New Password", type="password")
        if st.button("Confirm Password Change"):
            supabase.auth.update_user({"password": up_pw})
            st.success("Credentials updated.")
            
    # Link Email
    with st.expander("Update Email Address"):
        st.write(f"Current Identity: {email_current}")
        up_mail = st.text_input("New Email")
        if st.button("Link Email"):
            supabase.auth.update_user({"email": up_mail})
            st.info("Verification sent to new address.")

    if st.button("Logout", type="primary"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()
