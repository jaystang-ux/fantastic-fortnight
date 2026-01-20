import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_confetti import confetti

# 1. Database Connection
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Credential Error: Check Streamlit Secrets.")
    st.stop()

st.set_page_config(page_title="2026 Goals", page_icon="🎯", layout="centered")

# 2. Helper Functions
def fetch_data():
    res = supabase.table("resolutions").select("*").order("created_at").execute()
    return pd.DataFrame(res.data)

def update_progress(row_id, val, target):
    is_done = float(val) >= float(target)
    supabase.table("resolutions").update({
        "current_value": val, 
        "is_completed": is_done
    }).eq("id", row_id).execute()
    return is_done

def delete_goal(row_id):
    supabase.table("resolutions").delete().eq("id", row_id).execute()
    st.rerun()

# 3. Sidebar Input
with st.sidebar:
    st.header("New Resolution")
    new_title = st.text_input("Goal Name")
    new_cat = st.selectbox("Category", ["Health", "Finance", "Learning", "Personal"])
    new_type = st.radio("Method", ["Binary", "Numeric", "Percentage"])
    
    target_val = 1.0
    if new_type == "Numeric":
        target_val = st.number_input("Target", min_value=1.0, value=10.0)
    elif new_type == "Percentage":
        target_val = 100.0

    if st.button("Add Resolution", use_container_width=True):
        if new_title:
            supabase.table("resolutions").insert({
                "title": new_title, "category": new_cat,
                "tracking_type": new_type, "target_value": target_val
            }).execute()
            st.rerun()

# 4. Data Processing & Dashboard Header
df = fetch_data()

if not df.empty:
    total_goals = len(df)
    completed_goals = len(df[df['is_completed'] == True])
    
    st.title("🎯 Goal Tracker")
    
    # Progress Metric
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Completed", f"{completed_goals}")
    col_m2.metric("Total Goals", f"{total_goals}")
    
    st.progress(completed_goals / total_goals if total_goals > 0 else 0)
    st.markdown("---")
    
    # 5. Tabs for Organization
    tab1, tab2 = st.tabs(["🚀 Active Goals", "✅ Completed"])

    with tab1:
        active_df = df[df['is_completed'] == False]
        if active_df.empty:
            st.info("No active goals. Add one in the sidebar!")
        for _, row in active_df.iterrows():
            with st.expander(f"{row['title']}", expanded=True):
                prog = min(float(row['current_value']) / float(row['target_value']), 1.0)
                st.progress(prog)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    if row['tracking_type'] == "Binary":
                        if st.button("Complete", key=f"act_{row['id']}", use_container_width=True):
                            update_progress(row['id'], 1, 1)
                            confetti()
                            st.rerun()
                    else:
                        new_val = st.number_input("Update Value", value=float(row['current_value']), key=f"in_{row['id']}")
                        if new_val != row['current_value']:
                            if update_progress(row['id'], new_val, row['target_value']):
                                confetti()
                            st.rerun()
                with c2:
                    if st.button("🗑️", key=f"del_{row['id']}", help="Delete Goal"):
                        delete_goal(row['id'])

    with tab2:
        done_df = df[df['is_completed'] == True]
        if done_df.empty:
            st.write("No goals completed yet. Keep going!")
        for _, row in done_df.iterrows():
            col_d1, col_d2 = st.columns([4, 1])
            with col_d1:
                st.success(f"**{row['title']}** ({row['category']})")
            with col_d2:
                if st.button("🗑️", key=f"del_done_{row['id']}"):
                    delete_goal(row['id'])
else:
    st.title("🎯 Goal Tracker")
    st.info("Add a goal in the sidebar to begin.")
