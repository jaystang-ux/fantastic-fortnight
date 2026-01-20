import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_confetti import confetti

# 1. Database Connection Setup
# Ensure these keys are set in Streamlit Cloud Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Credential Error: Please check your Streamlit Secrets configuration.")
    st.stop()

# 2. Page Configuration for Mobile Responsiveness
st.set_page_config(
    page_title="2026 Resolutions", 
    page_icon="🎯", 
    layout="centered"
)

# 3. Data Management Functions
def fetch_data():
    try:
        res = supabase.table("resolutions").select("*").order("created_at").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

def update_progress(row_id, val, target):
    is_done = float(val) >= float(target)
    supabase.table("resolutions").update({
        "current_value": val, 
        "is_completed": is_done
    }).eq("id", row_id).execute()
    return is_done

# 4. Interface Header
st.title("🎯 Resolution Tracker")
st.markdown("---")

# 5. Sidebar: Input Form
with st.sidebar:
    st.header("New Resolution")
    new_title = st.text_input("Goal Name", placeholder="e.g., Read 12 Books")
    new_cat = st.selectbox("Category", ["Health", "Finance", "Learning", "Personal"])
    new_type = st.radio("Tracking Method", ["Binary (Done/Not Done)", "Numeric (Count)", "Percentage"])
    
    # Set target based on tracking type
    if "Binary" in new_type:
        target_val = 1.0
        db_type = "Binary"
    elif "Percentage" in new_type:
        target_val = 100.0
        db_type = "Percentage"
    else:
        target_val = st.number_input("Target Goal", min_value=1.0, value=10.0)
        db_type = "Numeric"
    
    if st.button("Add Resolution", use_container_width=True):
        if new_title:
            supabase.table("resolutions").insert({
                "title": new_title,
                "category": new_cat,
                "tracking_type": db_type,
                "target_value": target_val,
                "current_value": 0
            }).execute()
            st.rerun()
        else:
            st.warning("Please enter a title.")

# 6. Main Dashboard Logic
df = fetch_data()

if not df.empty:
    for _, row in df.iterrows():
        # Visual Card Container
        with st.expander(f"{'✅ ' if row['is_completed'] else '🚀 '} {row['title']}", expanded=not row['is_completed']):
            cols = st.columns([2, 1])
            
            with cols[0]:
                st.write(f"Category: **{row['category']}**")
                # Calculate progress percentage for the bar
                progress_pct = min(float(row['current_value']) / float(row['target_value']), 1.0)
                st.progress(progress_pct)
                st.caption(f"Progress: {row['current_value']} / {row['target_value']}")

            with cols[1]:
                if not row['is_completed']:
                    if row['tracking_type'] == "Binary":
                        if st.button("Complete", key=f"btn_{row['id']}", use_container_width=True):
                            update_progress(row['id'], 1, 1)
                            confetti()
                            st.rerun()
                    else:
                        step = 1.0 if row['tracking_type'] == "Numeric" else 5.0
                        new_val = st.number_input(
                            "Update", 
                            value=float(row['current_value']), 
                            step=step,
                            key=f"input_{row['id']}"
                        )
                        if new_val != row['current_value']:
                            if update_progress(row['id'], new_val, row['target_value']):
                                confetti()
                            st.rerun()
                else:
                    st.success("Completed")
else:
    st.info("No resolutions found. Use the sidebar to add your first goal.")
