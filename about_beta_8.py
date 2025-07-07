import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# -------------------------------
# Default Data
# -------------------------------

geo_df = pd.DataFrame({
    "Country": ["India", "United States", "United Kingdom", "Japan"],
    "ISO_Code": ["IND", "USA", "GBR", "JPN"],
    "Banking_Index": [
        "NIFTYBANK", "Dow Jones U.S. Banks Index",
        "FTSE 350 Banks Index", "TOPIX Banks Index"
    ],
    "Beta": [1.20, 1.10, 0.95, 0.85]
})

default_reference = {
    "en": {
        "Definition": "Beta measures the volatility of a stock or portfolio relative to market movements.",
        "Stock Use Case": "Used in CAPM to calculate expected return and evaluate market-driven risk.",
        "Portfolio Use Case": "Helps adjust portfolio exposure and supports strategic rebalancing."
    },
    "ta": {
        "Definition": "பீட்டா என்பது சந்தை இயக்கங்களை ஒப்பிடும் ஒரு பங்கு அல்லது போர்ட்ஃபோலியோவின் மாறுபாட்டை அளவிடும் ஒரு அளவீடு.",
        "Stock Use Case": "CAPM மூலம் எதிர்பார்க்கப்படும் வருமானம் மற்றும் சந்தை சார்ந்த அபாயத்தை கணக்கிட பயன்படுகிறது.",
        "Portfolio Use Case": "போர்ட்ஃபோலியோ உள்ளடக்கத்தை சரிசெய்யவும் மறுஉறுப்பாய்வை ஆதரிக்கவும் உதவுகிறது."
    },
    "hi": {
        "Definition": "बीटा बाजार की गति के सापेक्ष किसी स्टॉक या पोर्टफोलियो की अस्थिरता को मापता है।",
        "Stock Use Case": "CAPM में अपेक्षित रिटर्न की गणना और बाजार-प्रेरित जोखिम का मूल्यांकन करने में प्रयोग होता है।",
        "Portfolio Use Case": "पोर्टफोलियो एक्सपोज़र को समायोजित करने और पुनर्संतुलन में सहायक।"
    }
}

default_regional_summary = pd.DataFrame([
    {"Country": "India", "Index": "NIFTY Bank Index", "Beta Range": "1.2", "Volatility": "High Volatility", "Notes": "Sensitive to macroeconomic shifts"},
    {"Country": "USA", "Index": "Dow Jones Banking Index", "Beta Range": "0.52–0.88", "Volatility": "Moderate Volatility", "Notes": "Wide range by bank size"},
    {"Country": "UK", "Index": "FTSE Banks", "Beta Range": "0.6–1.0", "Volatility": "Moderate Volatility", "Notes": "Global vs domestic split"},
    {"Country": "Japan", "Index": "Tokyo Banks", "Beta Range": "<0.7", "Volatility": "Low Volatility", "Notes": "Stable, conservative lending model"}
])

# -------------------------------
# Streamlit Setup
# -------------------------------

st.set_page_config(layout="wide")
st.title("🌍 Global Banking Beta Dashboard")

st.sidebar.header("📂 Controls")
language = st.sidebar.selectbox("Language", ["en", "ta", "hi"], format_func=lambda x: {"en": "English", "ta": "Tamil", "hi": "Hindi"}[x])
regional_file = st.sidebar.file_uploader("Upload regional_summaries.json", type="json")
beta_file = st.sidebar.file_uploader("Upload beta_comparison.json", type="json")

bank_beta_df = pd.DataFrame()
insights_by_lang = {"en": {}, "ta": {}, "hi": {}}

# -------------------------------
# Load beta_comparison.json automatically if no upload
# -------------------------------

if not beta_file and os.path.exists("beta_comparison.json"):
    try:
        with open("beta_comparison.json", "r", encoding="utf-8") as f:
            bdata = json.load(f)
        beta_file = "loaded"
    except:
        bdata = {}

# -------------------------------
# Parse Input Files
# -------------------------------

if regional_file:
    try:
        rdata = json.load(regional_file)
        default_reference = {
            lang: {
                "Definition": rdata["definition"][lang],
                "Stock Use Case": rdata["use_cases"][lang]["stock"],
                "Portfolio Use Case": rdata["use_cases"][lang]["portfolio"]
            } for lang in ["en", "ta", "hi"]
        }
        default_regional_summary = pd.DataFrame(rdata["regional_summaries"])
    except Exception as e:
        st.warning(f"⚠️ Failed to load regional_summaries.json: {e}")

if beta_file:
    try:
        if isinstance(beta_file, str) and beta_file == "loaded":
            pass  # bdata already loaded
        else:
            bdata = json.load(beta_file)
        rows = []
        for country, val in bdata.items():
            for bank in val["Large_Cap_Banks"]:
                rows.append({
                    "Country": country,
                    "Index": val["Index"],
                    "Index Beta": val["Index_Beta"],
                    "Bank Name": bank["name"],
                    "Bank Beta": bank["beta"]
                })
            insights_by_lang["en"][country] = val.get("Insights", "")
            insights_by_lang["ta"][country] = val.get("Insights_TA", "")
            insights_by_lang["hi"][country] = val.get("Insights_HI", "")
        bank_beta_df = pd.DataFrame(rows)
    except Exception as e:
        st.warning(f"⚠️ Failed to parse beta_comparison.json: {e}")

# -------------------------------
# 1️⃣ Definition and Use Cases
# -------------------------------

st.subheader("📘 Beta Definition and Use Cases")
st.table(pd.DataFrame(default_reference[language].items(), columns=["Concept", "Content"]))

# -------------------------------
# 2️⃣ Beta Dispersion Map
# -------------------------------

st.subheader("📊 Beta Dispersion Map")
fig = px.choropleth(
    geo_df,
    locations="ISO_Code",
    color="Beta",
    hover_name="Banking_Index",
    hover_data={"Beta": True},
    color_continuous_scale="Reds",
    range_color=(0.8, 1.4),
    labels={"Beta": "Beta"}
)
fig.update_geos(projection_type="natural earth")
st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# 3️⃣ Regional Summary
# -------------------------------

st.subheader("🌐 Regional Beta Summary")
st.dataframe(default_regional_summary, use_container_width=True)

# -------------------------------
# 4️⃣ Index-wise Expandable Cards
# -------------------------------

if not bank_beta_df.empty:
    st.subheader("🗂️ Index-wise Beta Overview")
    grouped = bank_beta_df.groupby(["Index", "Index Beta"])

    for (idx, idx_beta), group in grouped:
        try:
            beta_val = float(str(idx_beta).split()[0].replace("<", "").replace(">", "").strip())
        except:
            beta_val = 1.0

        color = "#e0f3e0" if beta_val < 1.0 else "#fff2cc" if beta_val < 1.2 else "#ffcccc"
        country = group["Country"].iloc[0]
        insight_text = insights_by_lang.get(language, {}).get(country, "")

        with st.expander(f"📘 {idx} — Beta: {idx_beta}"):
            st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:6px'>"
                        f"<b>{country}</b>: {insight_text}</div>", unsafe_allow_html=True)
            st.dataframe(group[["Bank Name", "Bank Beta"]].reset_index(drop=True), use_container_width=True)

# -------------------------------
# 5️⃣ Filterable Bank Table + Insights
# -------------------------------

if not bank_beta_df.empty:
    st.subheader("🏦 Filter Bank Betas")
    col1, col2 = st.columns(2)
    sel_country = col1.selectbox("Select Country", ["All"] + sorted(bank_beta_df["Country"].unique()))
    sel_bank = col2.selectbox("Select Bank", ["All"] + sorted(
        bank_beta_df[bank_beta_df["Country"] == sel_country]["Bank Name"].unique()
        if sel_country != "All" else bank_beta_df["Bank Name"].unique()
    ))

    filtered_df = bank_beta_df.copy()
    if sel_country != "All":
        filtered_df = filtered_df[filtered_df["Country"] == sel_country]
    if sel_bank != "All":
        filtered_df = filtered_df[filtered_df["Bank Name"] == sel_bank]

    st.dataframe(filtered_df, use_container_width=True)

    if sel_country != "All":
        insight = insights_by_lang.get(language, {}).get(sel_country, "")
        if insight:
            st.markdown(f"🧠 **Insight for {sel_country}:**")
            st.info(insight)

# -------------------------------
# Footer
# -------------------------------

st.markdown("---")
st.markdown("Built with ❤️ using Streamlit · Powered by Copilot")
