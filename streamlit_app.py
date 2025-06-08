import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Ad ROI Dashboard", layout="wide")
sns.set_theme(style="whitegrid")

@st.cache_data
def load_data():
    costs = pd.read_csv("data/costs_us.csv")
    orders = pd.read_csv("data/orders_log_us.csv")
    visits = pd.read_csv("data/visits_log_us.csv")
    return costs, orders, visits

@st.cache_data

def preprocess(costs, orders, visits):
    # Prepare dates
    orders['date'] = pd.to_datetime(orders['Buy Ts']).dt.date
    visits['date'] = pd.to_datetime(visits['Start Ts']).dt.date
    costs['date'] = pd.to_datetime(costs['dt']).dt.date

    # Aggregate data
    orders_kpi = (
        orders.groupby(['date'])
        .agg({'Revenue': 'sum', 'Uid': 'count'})
        .rename(columns={'Uid': 'Orders'})
        .reset_index()
    )
    visits_kpi = (
        visits.groupby(['date'])
        .agg({'Uid': 'nunique'})
        .rename(columns={'Uid': 'Clicks'})
        .reset_index()
    )
    costs_kpi = (
        costs.groupby(['date'])
        .agg({'costs': 'sum'})
        .rename(columns={'costs': 'Cost'})
        .reset_index()
    )
    merged = costs_kpi.merge(visits_kpi, on='date', how='left').merge(orders_kpi, on='date', how='left')
    merged[['Clicks', 'Orders', 'Revenue']] = merged[['Clicks', 'Orders', 'Revenue']].fillna(0)
    merged['ROAS'] = merged['Revenue'] / merged['Cost']
    merged['CPC'] = merged['Cost'] / merged['Clicks']
    merged['Conversion Rate'] = merged['Orders'] / merged['Clicks']
    merged.replace([np.inf, -np.inf], np.nan, inplace=True)
    merged.fillna(0, inplace=True)
    return merged

# Load
costs, orders, visits = load_data()
merged = preprocess(costs, orders, visits)

# Tabs
summary_tab, trends_tab, device_tab, export_tab = st.tabs([
    "📊 KPI Summary", "📈 Trends", "🖥️ By Device", "⬇️ Export"])

with summary_tab:
    st.header("Key KPI Metrics")
    st.metric("Avg. ROAS", f"{merged['ROAS'].mean():.2f}")
    st.metric("Avg. CPC", f"{merged['CPC'].mean():.2f}")
    st.metric("Avg. Conversion Rate", f"{merged['Conversion Rate'].mean():.2%}")
    st.dataframe(merged.sort_values('date', ascending=False).head(20))

with trends_tab:
    st.header("Daily KPI Trends")
    fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    sns.lineplot(data=merged, x='date', y='ROAS', ax=ax[0])
    ax[0].set_title("ROAS")
    sns.lineplot(data=merged, x='date', y='CPC', ax=ax[1])
    ax[1].set_title("CPC")
    sns.lineplot(data=merged, x='date', y='Conversion Rate', ax=ax[2])
    ax[2].set_title("Conversion Rate")
    st.pyplot(fig)

with device_tab:
    st.header("Custom KPI Flagging")
    flags = (
        merged.groupby('date')[['CPC', 'ROAS']].mean()
        .reset_index()
    )
    flags['Flag'] = ''
    flags.loc[flags['CPC'] > 1.0, 'Flag'] += ' High CPC'
    flags.loc[flags['ROAS'] < 5.0, 'Flag'] += ' Low ROAS'
    st.dataframe(flags[flags['Flag'] != ''])

with export_tab:
    st.header("Download Full KPI Table")
    st.download_button("Download CSV", merged.to_csv(index=False), "kpi_summary.csv")
