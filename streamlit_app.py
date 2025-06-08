import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(layout="wide", page_title="Ad ROI Dashboard – Demo 3")

# Caching the data load for performance
@st.cache_data
def load_data():
    costs = pd.read_csv("data/costs_us.csv")
    orders = pd.read_csv("data/orders_log_us.csv")
    visits = pd.read_csv("data/visits_log_us.csv")
    return costs, orders, visits

costs, orders, visits = load_data()

# Preprocessing
def preprocess(costs, orders, visits):
    orders["date"] = pd.to_datetime(orders["Buy Ts"]).dt.date
    visits["date"] = pd.to_datetime(visits["Start Ts"]).dt.date
    costs["date"] = pd.to_datetime(costs["dt"]).dt.date
    costs = costs.rename(columns={"source_id": "Source Id", "costs": "Cost"})

    visits_orders = visits.merge(orders, on="Uid", how="left")
    visits_orders["date"] = pd.to_datetime(visits_orders["Start Ts"]).dt.date
    device_agg = visits_orders.groupby(["date", "Source Id", "Device"], as_index=False).agg({
        "Uid": "count",
        "Revenue": "sum",
        "Buy Ts": "count"
    }).rename(columns={"Uid": "Clicks", "Buy Ts": "Orders"})

    costs_agg = costs.groupby(["date", "Source Id"], as_index=False)["Cost"].sum()
    kpi = device_agg.merge(costs_agg, on=["date", "Source Id"], how="left")

    kpi["ROAS"] = kpi["Revenue"] / kpi["Cost"]
    kpi["CPC"] = kpi["Cost"] / kpi["Clicks"]
    kpi["Conversion Rate"] = kpi["Orders"] / kpi["Clicks"]
    kpi.replace([np.inf, -np.inf], np.nan, inplace=True)
    kpi.fillna(0, inplace=True)

    return kpi

kpi = preprocess(costs, orders, visits)

# Tabs
tabs = st.tabs(["📊 KPI Overview", "📈 Trends", "🔥 Source Flags", "📁 Export"])

# Tab 1 – KPI Overview
with tabs[0]:
    st.header("📊 KPI Metrics by Source & Device")
    summary = (
        kpi.groupby(["Source Id", "Device"])
        [["ROAS", "CPC", "Conversion Rate"]]
        .mean()
        .round(2)
        .reset_index()
    )
    st.dataframe(summary, use_container_width=True)

    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    sns.barplot(data=summary, x="Source Id", y="ROAS", hue="Device", ax=axes[0])
    sns.barplot(data=summary, x="Source Id", y="CPC", hue="Device", ax=axes[1])
    sns.barplot(data=summary, x="Source Id", y="Conversion Rate", hue="Device", ax=axes[2])
    axes[0].set_title("ROAS by Source & Device")
    axes[1].set_title("CPC by Source & Device")
    axes[2].set_title("Conversion Rate by Source & Device")
    st.pyplot(fig)

# Tab 2 – Trends
with tabs[1]:
    st.header("📈 KPI Trends Over Time")
    trend_metric = st.selectbox("Select KPI", ["ROAS", "CPC", "Conversion Rate"], index=0)
    st.line_chart(
        data=kpi.groupby(["date", "Source Id"])[trend_metric].mean().unstack().fillna(0),
        use_container_width=True
    )

# Tab 3 – Flags
with tabs[2]:
    st.header("🔥 Flagged Sources (High CPC or Low ROAS)")
    flagged = (
        kpi.groupby("Source Id")[["CPC", "ROAS"]].mean().round(2).reset_index()
    )
    flagged["Flag"] = ""
    flagged.loc[flagged["CPC"] > 1.0, "Flag"] += "High CPC "
    flagged.loc[flagged["ROAS"] < 5, "Flag"] += "Low ROAS"
    flagged = flagged[flagged["Flag"] != ""]

    st.dataframe(flagged.style.background_gradient(cmap="OrRd", subset=["CPC", "ROAS"]),
                 use_container_width=True)

# Tab 4 – Export
with tabs[3]:
    st.header("📁 Export KPI Summary")
    if st.button("Download Merged KPI CSV"):
        csv = kpi.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="kpi_summary.csv",
            mime="text/csv"
        )
    st.dataframe(kpi.head(50), use_container_width=True)
