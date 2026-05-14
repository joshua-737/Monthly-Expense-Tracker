# THE BABYLON VAULT
# Engineered for pure capital allocation.

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import re
from datetime import datetime
from pathlib import Path

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="The Babylon Vault", page_icon="🏛️")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1F2937;
    }
    
    .stApp { background-color: #FFFFFF; }
    
    .metric-card {
        background-color: #F3F4F6;
        padding: 2rem;
        border-radius: 1rem;
        border-left: none;
        transition: all 0.3s ease;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        color: #1F2937;
        margin-bottom: 0.5rem;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #9CA3AF;
        letter-spacing: 0.1em;
    }
    
    .gold-accent { color: #B8956A !important; }
    .gold-border { border-left: 4px solid #B8956A !important; }
</style>
""", unsafe_allow_html=True)

# --- DATA PERSISTENCE ---
DATA_DIR = Path.home() / ".streamlit_vault"
DATA_FILE = DATA_DIR / "expenses.json"

def init_storage():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        with open(DATA_FILE, "w") as f:
            json.dump({"expenses": [], "capital": 0.0}, f)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"expenses": [], "capital": 0.0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- SESSION STATE ---
if "vault_data" not in st.session_state:
    init_storage()
    st.session_state.vault_data = load_data()

# --- INPUT PARSING ---
def categorize_input(text):
    text = text.lower()
    
    needs = ['food', 'pani puri', 'biryani', 'chai', 'tea', 'coffee', 'groceries', 'bus', 'auto', 'cab', 'petrol', 'rent', 'electricity', 'internet', 'medicine', 'hospital', 'college', 'books']
    wants = ['projector', 'gaming', 'ps5', 'netflix', 'spotify', 'movie', 'luxury', 'zomato', 'swiggy', 'pizza', 'gadget', 'travel', 'gym']
    savings = ['invest', 'stocks', 'mutual fund', 'sip', 'gold', 'crypto']
    
    for word in savings:
        if word in text: return "SAVINGS/INVESTMENT"
    for word in needs:
        if word in text: return "NEEDS"
    for word in wants:
        if word in text: return "WANTS"
    
    return "MISCELLANEOUS"

def process_input(user_input):
    amount_match = re.search(r"(\d+(\.\d+)?)", user_input)
    if not amount_match:
        return None
    
    amount = float(amount_match.group(1))
    desc = user_input.replace(amount_match.group(0), "").strip()
    if desc.lower().startswith("for"):
        desc = desc[3:].strip()
    
    if not desc: desc = "Manual Entry"
    cat = categorize_input(desc)
    
    return {
        "id": str(datetime.now().timestamp()),
        "amount": amount,
        "description": desc,
        "category": cat,
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M")
    }

# --- HEADER & CAPITAL ---
col_head, col_cap = st.columns([3, 1])
with col_head:
    st.title("🏛️ The Babylon Vault")
    st.caption("A portion of all you earn is yours to keep.")

with col_cap:
    new_capital = st.number_input("Update My Capital (₹)", 
                                 value=float(st.session_state.vault_data["capital"]),
                                 step=1000.0,
                                 format="%f")
    if new_capital != st.session_state.vault_data["capital"]:
        st.session_state.vault_data["capital"] = new_capital
        save_data(st.session_state.vault_data)
        st.rerun()

# --- METRICS & MATH LOGIC ---
expenses = st.session_state.vault_data["expenses"]
total_cap = st.session_state.vault_data["capital"]

# First Principle Constraints
gold_future = total_cap * 0.10
wealth_built = sum(e["amount"] for e in expenses if e["category"] == "SAVINGS/INVESTMENT")
money_burned = sum(e["amount"] for e in expenses if e["category"] in ["NEEDS", "WANTS", "MISCELLANEOUS"])
spendable = total_cap - gold_future - money_burned

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">₹{total_cap:,.0f}</div><div class="metric-label">Total Capital</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card gold-border"><div class="metric-value gold-accent">₹{gold_future:,.0f}</div><div class="metric-label gold-accent">Untouchable Seed</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-value">₹{spendable:,.0f}</div><div class="metric-label">Spendable Balance</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><div class="metric-value gold-accent">₹{wealth_built:,.0f}</div><div class="metric-label">Wealth Built</div></div>', unsafe_allow_html=True)

st.markdown("---")

# --- THE INPUT ENGINE ---
user_query = st.chat_input("Enter transaction: e.g. 40 for pani puri or 5000 for SIP")

if user_query:
    entry = process_input(user_query)
    if entry:
        st.session_state.vault_data["expenses"].insert(0, entry)
        save_data(st.session_state.vault_data)
        st.rerun()

# --- LEDGER ---
t_lifetime, t_month = st.tabs(["Lifetime View", "Current Month View"])

df = pd.DataFrame(expenses)
if not df.empty:
    df["dt"] = pd.to_datetime(df["timestamp"], format="%d-%m-%Y %H:%M")
    current_month_mask = (df["dt"].dt.month == datetime.now().month) & (df["dt"].dt.year == datetime.now().year)
    
    with t_lifetime:
        st.dataframe(df[["timestamp", "description", "category", "amount"]].rename(columns={"timestamp": "Date", "amount": "Amount (₹)"}), use_container_width=True)
    
    with t_month:
        month_df = df[current_month_mask]
        st.dataframe(month_df[["timestamp", "description", "category", "amount"]].rename(columns={"timestamp": "Date", "amount": "Amount (₹)"}), use_container_width=True)

# --- INLINE LEDGER CONTROLS (THE FIX) ---
st.markdown("### Active Ledger")

if st.session_state.vault_data["expenses"]:
    h1, h2, h3, h4 = st.columns([2, 4, 2, 1])
    h1.caption("DATE")
    h2.caption("DESCRIPTION")
    h3.caption("AMOUNT")
    h4.caption("ACTION")
    st.divider()

    for exp in st.session_state.vault_data["expenses"]:
        c1, c2, c3, c4 = st.columns([2, 4, 2, 1])
        c1.write(exp["timestamp"].split(" ")[0]) 
        c2.write(exp["description"].title())
        c3.write(f"₹{exp['amount']}")
        
        if c4.button("❌", key=f"kill_{exp['id']}"):
            st.session_state.vault_data["expenses"] = [e for e in st.session_state.vault_data["expenses"] if e["id"] != exp["id"]]
            save_data(st.session_state.vault_data)
            st.rerun()
            
    st.divider()
    if st.button("🚨 PURGE ALL DATA", type="primary", use_container_width=True):
        st.session_state.vault_data["expenses"] = []
        save_data(st.session_state.vault_data)
        st.rerun()
else:
    st.info("Ledger is clean.")

st.markdown("---")

# --- ANALYTICS ---
st.subheader("The Oracle — Monthly Insights")
if not df.empty:
    c1, c2 = st.columns(2)
    
    with c1:
        df_chart = df[df["category"] != "SAVINGS/INVESTMENT"].copy()
        if not df_chart.empty:
            df_chart["Month"] = df_chart["dt"].dt.strftime("%b %Y")
            monthly_stats = df_chart.groupby(["Month", "category"])["amount"].sum().reset_index()
            fig_bar = px.bar(monthly_stats, x="Month", y="amount", color="category", barmode="group",
                             color_discrete_map={"NEEDS": "#64748B", "WANTS": "#A78BBA", "MISCELLANEOUS": "#BEBEC4"},
                             template="plotly_white", title="Monthly Burn Rate")
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.write("No burn data to chart.")
        
    with c2:
        pie_data = df.groupby("category")["amount"].sum().reset_index()
        fig_pie = px.pie(pie_data, values="amount", names="category", hole=0.7,
                         color="category", color_discrete_map={"NEEDS": "#64748B", "WANTS": "#A78BBA", "MISCELLANEOUS": "#BEBEC4", "SAVINGS/INVESTMENT": "#D4A574"},
                         template="plotly_white", title="Capital Allocation")
        st.plotly_chart(fig_pie, use_container_width=True)

    # WEALTH REPORT
    st.markdown("### Structural Integrity")
    
    current_month_df = df[current_month_mask]
    cm_wants = current_month_df[current_month_df["category"] == "WANTS"]["amount"].sum()
    cm_needs = current_month_df[current_month_df["category"] == "NEEDS"]["amount"].sum()
    
    if spendable > 0:
        if cm_wants > (spendable * 0.2):
            st.error("WARNING: WANTS EXCEED 20% OF LIQUIDITY. Control your expenditures.")
        if cm_needs > (total_cap * 0.7):
            st.warning("WARNING: SURVIVAL COSTS EXCEED 70%. Increase top-line revenue immediately.")
        if cm_wants <= (spendable * 0.2) and (cm_needs + cm_wants) > 0:
            st.success("Burn rate optimal. Allocation holds.")
    else:
        st.error("LIQUIDITY DEPLETED. Cease spending immediately.")

else:
    st.info("Insufficient data to run diagnostics.")

st.markdown("---")
st.center = st.markdown("<p style='text-align: center; color: #9CA3AF; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.3em;'>BUILT ON FIRST PRINCIPLES</p>", unsafe_allow_html=True)
