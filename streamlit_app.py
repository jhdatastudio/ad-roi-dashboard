import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Streamlit & seaborn setup
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
    # Dates
    orders['date'] = pd.to_datetime(orders['Buy Ts']).dt.date
    visits['date'] = pd.to_datetime(visits['Start Ts']).dt.date
    costs['date'] = pd.to_datetime(costs['dt']).dt.date

    # Aggregate Orders
    orders_kpi = (
        orders.groupby('date')
        .agg(Revenue=('Revenue', 'sum'), Orders=('Uid', 'count'))
        .reset_index()
    )

    # Aggregate Visits
    visits_kpi = (
        visits.groupby('date')
        .agg(Clicks=('Uid', 'nunique'))
        .reset_index()
    )

    # Aggregate Costs
    costs_kpi = (
        costs.groupby('date')
        .agg(Cost=('costs', 'sum'))
        .reset_index()
    )

    # Merge
    merged = (
        costs_kpi
        .merge(visits_kpi, on='date', how='left')
        .merge(orders_kpi, on='date', how='left')
    )

    # Clean and Calculate
    merged[['Clicks', 'Orders', 'Revenue']] = merged[['Clicks', 'Orders', 'Revenue']].fillna(0)
    merged['ROAS'] = merged['Revenue'] / merged['Cost']
    merged['CPC'] = merged['Cost'] / merged['Clicks']
    merged['Conversion Rate'] = merged['Orders'] / merged['Clicks']
    merged.replace([np.inf, -np.inf], np.nan, inplace=True)
    merged.fillna(0, inplace=True)
    return merged

# Load and preprocess
costs, orders, visits = load_data()
merged = preprocess(costs, orders, visits)

# UI Tabs
summary_tab, trends_tab, flags_tab, export_tab = st.tabs([
    "📊 KPI Summary", "📈 Trends", "⚠️ Flagged Sources", "⬇️ Export Data"
])

with summary_tab:
    st.header("📊 KPI Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg. ROAS", f"{merged['ROAS'].mean():.2f}")
    col2.metric("Avg. CPC", f"{merged['CPC'].mean():.2f}")
    col3.metric("Conversion Rate", f"{merged['Conversion Rate'].mean():.2%}")
    st.dataframe(merged.sort_values('date', ascending=False).head(20), use_container_width=True)

with trends_tab:
    st.header("📈 Daily KPI Trends")
    fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    sns.lineplot(data=merged, x='date', y='ROAS', ax=ax[0])
    ax[0].set_title("ROAS")
    sns.lineplot(data=merged, x='date', y='CPC', ax=ax[1])
    ax[1].set_title("CPC")
    sns.lineplot(data=merged, x='date', y='Conversion Rate', ax=ax[2])
    ax[2].set_title("Conversion Rate")
    plt.xticks(rotation=45)
    st.pyplot(fig)

with flags_tab:
    st.header("⚠️ Flagged Sources (High CPC / Low ROAS)")

    kpi_flags = (
        merged.groupby('date')[['CPC', 'ROAS']].mean()
        .round(3)
        .reset_index()
    )
    kpi_flags['Flag'] = ''
    kpi_flags.loc[kpi_flags['CPC'] > 1.0, 'Flag'] += ' High CPC'
    kpi_flags.loc[kpi_flags['ROAS'] < 5.0, 'Flag'] += ' Low ROAS'
    flagged = kpi_flags[kpi_flags['Flag'].str.strip() != '']

    st.dataframe(flagged.style.background_gradient(cmap='OrRd', subset=['CPC', 'ROAS']), use_container_width=True)

with export_tab:
    st.header("⬇️ Download KPI Table")
    st.download_button("Download CSV", merged.to_csv(index=False), file_name="kpi_summary.csv", mime='text/csv')
