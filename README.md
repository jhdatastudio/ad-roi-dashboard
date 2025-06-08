# 📈 Ad ROI Dashboard – Demo 3

This Streamlit app analyzes marketing performance across digital ad sources and device types using real-world e-commerce data. It helps uncover cost-efficiency patterns and ROI anomalies to support budget decisions.

## 🔍 Objective
Evaluate advertising ROAS, CPC, and conversion efficiency across channels and devices.

## 📦 Dataset
This demo uses anonymized marketing data from a U.S.-based e-commerce platform from Kaggle:
- `costs_us.csv`: Daily ad spend by source
- `orders_log_us.csv`: Purchase revenue and UIDs
- `visits_log_us.csv`: Website visits with device type and ad source

## 🧮 Key Metrics
- **ROAS** = Revenue / Cost
- **CPC** = Cost / Click
- **Conversion Rate** = Orders / Clicks

## 🧭 App Features
| Tab | Description |
| --- | ----------- |
| **📊 KPI Overview** | Interactive bar charts and tables comparing ROAS, CPC, and conversion by Source & Device |
| **📈 Trends** | Daily ROAS and Conversion Rate trends by source |
| **🔥 Source Flags** | Highlights sources with High CPC or Low ROAS using custom thresholds |
| **📁 Export** | One-click CSV download of the aggregated KPI summary |


