# THE BABYLON VAULT - V3.0
# Month-by-Month Math Engine + Global Observability

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
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1F2937; }
    .stApp { background-color: #FFFFFF; }
    .metric-card { background-color: #F3F4F6; padding: 1.5rem; border-radius: 1rem; transition: all 0.3s ease; }
    .metric-value { font-size: 2.2rem; font-weight: 900; color: #1F2937; margin-bottom: 0.5rem; line-height: 1; }
    .metric-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #9CA3AF; letter-spacing: 0.1em; }
    .gold-accent { color: #B8956A !important; }
    .gold-border { border-left: 4px solid #B8956A !important; }
    .red-accent { color: #DC2626 !important; }
</style>
""", unsafe_allow_html=True)

# --- DATA ENGINE ---
DATA_DIR = Path.home() / ".streamlit_vault"
DATA_FILE = DATA_DIR / "expenses.json"

def init_storage():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        with open(DATA_FILE, "w") as f:
            json.dump({"expenses": [], "monthly_capital": {}}, f)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "monthly_capital" not in data:
                current_m = datetime.now().strftime("%b %Y")
                data["monthly_capital"] = {current_m: data.get("capital", 0.0)}
            return data
    except:
        return {"expenses": [], "monthly_capital": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

if "vault_data" not in st.session_state:
    init_storage()
    st.session_state.vault_data = load_data()

# --- PARSING ENGINE ---
def categorize_input(text):
    text = text.lower()
    needs = ['food', 'pani puri', 'biryani', 'chai', 'tea', 'coffee', 'groceries', 'bus', 'auto', 'cab', 'petrol', 'rent', 'electricity', 'internet', 'medicine', 'college', 'books']
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
    if not amount_match: return None
    
    amount = float(amount_match.group(1))
    desc = user_input.replace(amount_match.group(0), "").strip()
    if desc.lower().startswith("for"): desc = desc[3:].strip()
    if not desc: desc = "Manual Entry"
    
    return {
        "id": str(datetime.now().timestamp()),
        "amount": amount,
        "description": desc,
        "category": categorize_input(desc),
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M")
    }

# --- TIME CONTROLS (SIDEBAR) ---
expenses = st.session_state.vault_data["expenses"]
df = pd.DataFrame(expenses)

current_month_str = datetime.now().strftime("%b %Y")
available_months = [current_month_str]
if not df.empty:
    df["dt"] = pd.to_datetime(df["timestamp"], format="%d-%m-%Y %H:%M")
    data_months = df["dt"].dt.strftime("%b %Y").unique().tolist()
    available_months = list(set(available_months + data_months))
    available_months.sort(key=lambda date: datetime.strptime(date, "%b %Y"), reverse=True)

st.sidebar.title("⏳ Time Controls")
selected_month = st.sidebar.selectbox("Select Operating Month", available_months)

if not df.empty:
    month_df = df[df["dt"].dt.strftime("%b %Y") == selected_month]
else:
    month_df = pd.DataFrame()

# --- HEADER & MONTHLY CAPITAL ---
col_head, col_cap = st.columns([3, 1])
with col_head:
    st.title(f"🏛️ The Babylon Vault — {selected_month}")

with col_cap:
    current_cap = st.session_state.vault_data["monthly_capital"].get(selected_month, 0.0)
    new_capital = st.number_input("Monthly Income (₹)", value=float(current_cap), step=1000.0, format="%f")
    
    if new_capital != current_cap:
        st.session_state.vault_data["monthly_capital"][selected_month] = new_capital
        save_data(st.session_state.vault_data)
        st.rerun()

# --- STRICT ACCOUNTING LOGIC ---
if not month_df.empty:
    wealth_built = month_df[month_df["category"] == "SAVINGS/INVESTMENT"]["amount"].sum()
    money_burned = month_df[month_df["category"].isin(["NEEDS", "WANTS", "MISCELLANEOUS"])]["amount"].sum()
else:
    wealth_built = 0.0
    money_burned = 0.0

target_seed = new_capital * 0.10
spendable_allowance = new_capital * 0.90

idle_seed = target_seed - wealth_built
if idle_seed < 0:
    spendable_allowance += idle_seed 
    idle_seed = 0

spendable_remaining = spendable_allowance - money_burned

# --- METRICS UI ---
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">₹{new_capital:,.0f}</div><div class="metric-label">Monthly Income</div></div>', unsafe_allow_html=True)
with m2:
    seed_color = "gold-accent" if idle_seed > 0 else "red-accent"
    seed_label = "Idle Seed (Invest This!)" if idle_seed > 0 else "Seed Deployed"
    st.markdown(f'<div class="metric-card gold-border"><div class="metric-value {seed_color}">₹{idle_seed:,.0f}</div><div class="metric-label {seed_color}">{seed_label}</div></div>', unsafe_allow_html=True)
with m3:
    spend_color = "red-accent" if spendable_remaining < 0 else ""
    st.markdown(f'<div class="metric-card"><div class="metric-value {spend_color}">₹{spendable_remaining:,.0f}</div><div class="metric-label">Spendable Balance</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><div class="metric-value gold-accent">₹{wealth_built:,.0f}</div><div class="metric-label">Wealth Built (This Month)</div></div>', unsafe_allow_html=True)

st.markdown("---")

# --- THE INPUT ENGINE ---
user_query = st.chat_input(f"Enter transaction for {selected_month}: e.g. 40 for pani puri or 5000 for SIP")

if user_query:
    entry = process_input(user_query)
    if entry:
        current_dt = datetime.now()
        target_month_dt = datetime.strptime(selected_month, "%b %Y")
        if target_month_dt.month != current_dt.month or target_month_dt.year != current_dt.year:
            entry["timestamp"] = f"01-{target_month_dt.month:02d}-{target_month_dt.year} 12:00"
            
        st.session_state.vault_data["expenses"].insert(0, entry)
        save_data(st.session_state.vault_data)
        st.rerun()

# --- THE OBSERVABILITY DECK (TABS RESTORED) ---
t_month, t_lifetime, t_manage = st.tabs([f"📊 {selected_month} Ledger", "🌍 Lifetime Tracker", "⚠️ Danger Zone"])

with t_month:
    if not month_df.empty:
        st.dataframe(month_df[["timestamp", "description", "category", "amount"]].rename(columns={"timestamp": "Date", "description": "Item", "amount": "Cost (₹)"}), use_container_width=True, hide_index=True)
    else:
        st.info("No activity logged for this month.")

with t_lifetime:
    if not df.empty:
        st.dataframe(df[["timestamp", "description", "category", "amount"]].rename(columns={"timestamp": "Date", "description": "Item", "amount": "Cost (₹)"}), use_container_width=True, hide_index=True)
    else:
        st.info("No historical data found.")

with t_manage:
    st.markdown("### Delete Specific Entries")
    if st.session_state.vault_data["expenses"]:
        for exp in st.session_state.vault_data["expenses"][:50]: # Limits display to last 50 for performance
            c1, c2, c3, c4 = st.columns([2, 4, 2, 1])
            c1.write(exp["timestamp"].split(" ")[0]) 
            c2.write(exp["description"].title())
            c3.write(f"₹{exp['amount']}")
            if c4.button("❌ Delete", key=f"del_{exp['id']}"):
                st.session_state.vault_data["expenses"] = [e for e in st.session_state.vault_data["expenses"] if e["id"] != exp["id"]]
                save_data(st.session_state.vault_data)
                st.rerun()
        
        st.divider()
        if st.button("🚨 PURGE ALL DATA GLOBALLY", type="primary"):
            st.session_state.vault_data["expenses"] = []
            st.session_state.vault_data["monthly_capital"] = {}
            save_data(st.session_state.vault_data)
            st.rerun()
    else:
        st.info("Ledger is clean.")

st.markdown("---")

# --- ANALYTICS ---
if not month_df.empty:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### Allocation ({selected_month})")
        pie_data = month_df.groupby("category")["amount"].sum().reset_index()
        fig_pie = px.pie(pie_data, values="amount", names="category", hole=0.7,
                         color="category", color_discrete_map={"NEEDS": "#64748B", "WANTS": "#A78BBA", "MISCELLANEOUS": "#BEBEC4", "SAVINGS/INVESTMENT": "#D4A574"},
                         template="plotly_white")
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.markdown("#### Structural Integrity")
        cm_wants = month_df[month_df["category"] == "WANTS"]["amount"].sum()
        cm_needs = month_df[month_df["category"] == "NEEDS"]["amount"].sum()
        
        if spendable_allowance > 0:
            if cm_wants > (spendable_allowance * 0.2):
                st.error("WARNING: WANTS EXCEED 20% OF ALLOWANCE. Control your expenditures.")
            if cm_needs > (new_capital * 0.7):
                st.warning("WARNING: SURVIVAL COSTS EXCEED 70%. Increase top-line revenue.")
            if cm_wants <= (spendable_allowance * 0.2) and (cm_needs + cm_wants) > 0:
                st.success("Burn rate optimal. Allocation holds.")
        else:
            st.error("LIQUIDITY DEPLETED. Cease spending immediately.")
