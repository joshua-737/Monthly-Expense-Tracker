# THE BABYLON VAULT
# Personal Expense Tracker inspired by The Richest Man in Babylon
#
# DEPLOYMENT INSTRUCTIONS:
# For Streamlit Cloud (Online):
# 1. Push app.py and requirements.txt to a GitHub repo
# 2. Go to share.streamlit.io, connect GitHub, select repo and app.py
# 3. Share the public link with anyone
#
# For Standalone Executable (Downloadable):
# 1. Install PyInstaller: pip install pyinstaller
# 2. Package into .exe (Windows) or .app (Mac) using PyInstaller
# 3. Users download and run directly without needing Python installed
# 4. Data persists locally in ~/.streamlit_vault/expenses.json

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
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
    
    .stApp {
        background-color: #FFFFFF;
    }
    
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
    
    .gold-accent {
        color: #B8956A !important;
    }
    
    .gold-border {
        border-left: 4px solid #B8956A !important;
    }
    
    div[data-testid="stMetric"] {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 1rem;
    }
    
    .stDataFrame {
        border-radius: 1rem;
        overflow: hidden;
    }
    
    .wisdom-card {
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
    }
    
    .wisdom-needs { background-color: #FEF3C7; color: #92400E; }
    .wisdom-success { background-color: #ECFDF5; color: #065F46; }
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
    
    needs = ['food', 'pani puri', 'biryani', 'chai', 'tea', 'coffee', 'meals', 'breakfast', 'lunch', 'dinner', 'snacks', 'groceries', 'vegetables', 'fruits', 'rice', 'dal', 'bread', 'eggs', 'milk', 'butter', 'oil', 'spices', 'bus', 'auto', 'rickshaw', 'cab', 'ola', 'uber', 'train', 'metro', 'commute', 'transport', 'petrol', 'diesel', 'fuel', 'bike', 'car', 'vehicle', 'parking', 'rent', 'house', 'apartment', 'accommodation', 'bills', 'electricity', 'water', 'gas', 'cylinder', 'internet', 'mobile', 'phone', 'recharge', 'landline', 'medicine', 'hospital', 'doctor', 'pharmacy', 'chemist', 'health', 'medical', 'dental', 'clinic', 'healthcare', 'school', 'college', 'tuition', 'fees', 'education', 'books', 'stationery', 'notebook', 'pen', 'study', 'exam', 'maintenance', 'repair', 'plumbing', 'electrical', 'carpentry', 'cleaning']
    wants = ['projector', 'gaming', 'console', 'controller', 'steam', 'game', 'ps5', 'xbox', 'nintendo', 'netflix', 'amazon prime', 'hotstar', 'spotify', 'disney+', 'subscription', 'streaming', 'music', 'clothes', 'shoes', 'sneakers', 'shirt', 'pants', 'dress', 'jeans', 'fashion', 'apparel', 'accessories', 'party', 'club', 'hangout', 'outing', 'entertainment', 'movie', 'cinema', 'theatre', 'shows', 'concert', 'luxury', 'premium', 'expensive', 'high-end', 'branded', 'designer', 'zomato', 'swiggy', 'blinkit', 'zepto', 'restaurant', 'cafe', 'coffee shop', 'ice cream', 'dessert', 'chocolate', 'chips', 'junk food', 'fast food', 'mcdonalds', 'kfc', 'burger', 'pizza', 'delivery', 'gadget', 'headphones', 'earphones', 'airpods', 'keyboard', 'mouse', 'monitor', 'phone', 'laptop', 'tablet', 'electronics', 'device', 'watch', 'ring', 'jewelry', 'necklace', 'bracelet', 'accessories', 'gift', 'toy', 'decoration', 'hobby', 'art', 'craft', 'diy', 'alcohol', 'cigarette', 'tobacco', 'vape', 'smoking', 'salon', 'spa', 'haircut', 'skincare', 'makeup', 'perfume', 'grooming', 'cosmetics', 'beauty', 'travel', 'trip', 'vacation', 'hotel', 'resort', 'flight', 'booking', 'tourism', 'getaway', 'sports', 'gym', 'yoga', 'fitness', 'equipment', 'gear', 'training', 'workshop', 'class']
    savings = ['invest', 'stocks', 'mutual fund', 'sip', 'gold', 'crypto', 'bitcoin', 'ethereum', 'nft', 'fd', 'fixed deposit', 'savings', 'deposit', 'nps', 'ppf', 'insurance', 'pension', 'retirement', 'provident fund', 'bond']
    
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

# --- METRICS ---
expenses = st.session_state.vault_data["expenses"]
total_cap = st.session_state.vault_data["capital"]
gold_future = total_cap * 0.1
wealth_built = sum(e["amount"] for e in expenses if e["category"] == "SAVINGS/INVESTMENT")
total_spent = sum(e["amount"] for e in expenses)
spendable = total_cap - gold_future - total_spent

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

# --- INPUT ---
unique_past_descs = list(set([e["description"] for e in expenses]))

user_query = st.text_input("", placeholder="e.g. 40 for pani puri or 5000 for SIP", key="input_field")

# Logic for suggestions
if user_query and len(user_query) >= 2:
    q_parts = user_query.lower().split()
    last_word = q_parts[-1]
    matches = [d for d in unique_past_descs if last_word in d.lower() and d.lower() != last_word][:4]
    
    if matches:
        st.caption("Past Wisdom: " + ", ".join(f"`{m}`" for m in matches))
        cols_sug = st.columns(len(matches) + 1)
        for i, m in enumerate(matches):
            if cols_sug[i].button(m, key=f"sug_{i}", use_container_width=True):
                # Apply suggestion
                amount_match = re.search(r"(\d+(\.\d+)?)", user_query)
                if amount_match:
                    st.session_state.input_field = f"{amount_match.group(0)} for {m}"
                else:
                    st.session_state.input_field = m
                st.rerun()

if user_query:
    entry = process_input(user_query)
    if entry:
        st.session_state.vault_data["expenses"].insert(0, entry)
        save_data(st.session_state.vault_data)
        st.success(f"Loged ₹{entry['amount']} for {entry['description']} under {entry['category']}")
        st.rerun()

st.markdown("---")

# --- LEDGER ---
t_lifetime, t_month = st.tabs(["Lifetime View", "Current Month View"])

df = pd.DataFrame(expenses)
if not df.empty:
    df["dt"] = pd.to_datetime(df["timestamp"], format="%d-%m-%Y %H:%M")
    current_month_mask = (df["dt"].dt.month == datetime.now().month) & (df["dt"].dt.year == datetime.now().year)
    
    with t_lifetime:
        st.dataframe(df[["timestamp", "description", "category", "amount"]].rename(columns={"timestamp": "Date", "amount": "Amount (₹)"}), use_container_width=True)
        st.markdown(f"**Total Used (Lifetime): ₹{df['amount'].sum():,.2f}**")
    
    with t_month:
        month_df = df[current_month_mask]
        st.dataframe(month_df[["timestamp", "description", "category", "amount"]].rename(columns={"timestamp": "Date", "amount": "Amount (₹)"}), use_container_width=True)
        st.markdown(f"**Total Used (This Month): ₹{month_df['amount'].sum():,.2f}**")

    # Actions
    with st.expander("Manage Records"):
        col_ed_ix, col_ed_btn = st.columns([3,1])
        target_id = st.selectbox("Select Record to Delete", options=[e["id"] for e in expenses], format_func=lambda x: next(i["description"] + " (₹" + str(i["amount"]) + ")" for i in expenses if i["id"] == x))
        if st.button("Delete Selected Record", type="primary"):
            st.session_state.vault_data["expenses"] = [e for e in expenses if e["id"] != target_id]
            save_data(st.session_state.vault_data)
            st.rerun()
        
        if st.button("Clear All Expenses"):
            if st.checkbox("Confirm Complete Wipe"):
                st.session_state.vault_data["expenses"] = []
                save_data(st.session_state.vault_data)
                st.rerun()
else:
    st.info("The ledger is empty. Start thy journey.")

st.markdown("---")

# --- ANALYTICS ---
st.subheader("The Oracle — Monthly Insights")
if not df.empty:
    c1, c2 = st.columns(2)
    
    with c1:
        # Bar Chart
        df_chart = df[df["category"] != "SAVINGS/INVESTMENT"].copy()
        df_chart["Month"] = df_chart["dt"].dt.strftime("%b %Y")
        monthly_stats = df_chart.groupby(["Month", "category"])["amount"].sum().reset_index()
        fig_bar = px.bar(monthly_stats, x="Month", y="amount", color="category", barmode="group",
                         color_discrete_map={"NEEDS": "#64748B", "WANTS": "#A78BBA", "MISCELLANEOUS": "#BEBEC4"},
                         template="plotly_white", title="Monthly Spending Breakdown")
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c2:
        # Pie Chart
        pie_data = df.groupby("category")["amount"].sum().reset_index()
        fig_pie = px.pie(pie_data, values="amount", names="category", hole=0.7,
                         color="category", color_discrete_map={"NEEDS": "#64748B", "WANTS": "#A78BBA", "MISCELLANEOUS": "#BEBEC4", "SAVINGS/INVESTMENT": "#D4A574"},
                         template="plotly_white", title="Lifetime Breakdown")
        st.plotly_chart(fig_pie, use_container_width=True)

    # WEALTH REPORT
    st.markdown("### Wealth Report")
    
    current_month_df = df[current_month_mask]
    cm_wants = current_month_df[current_month_df["category"] == "WANTS"]["amount"].sum()
    cm_needs = current_month_df[current_month_df["category"] == "NEEDS"]["amount"].sum()
    cm_inv = current_month_df[current_month_df["category"] == "SAVINGS/INVESTMENT"]["amount"].sum()
    
    if cm_wants > (spendable * 0.2):
        st.warning("Thy purse is leaking! The rich man controls his expenditures. (Wants > 20% of balance)")
    if cm_needs > (total_cap * 0.7):
        st.warning("Thou art surviving, not building. Seek ways to grow thy income. (Needs > 70% of capital)")
    if cm_wants < (spendable * 0.2) and (cm_needs + cm_wants) > 0:
        st.success("Well done. A portion of all you earn is yours to keep. The walls of Babylon hold.")
    if wealth_built > 0:
        st.success("A man who builds wealth first pays himself. Babylon smiles upon thee.")

else:
    st.info("Log thy first expense to see the Oracle's wisdom.")

st.markdown("---")
st.center = st.markdown("<p style='text-align: center; color: #9CA3AF; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.3em;'>The Richest Man in Babylon • Built for Thee</p>", unsafe_allow_html=True)
