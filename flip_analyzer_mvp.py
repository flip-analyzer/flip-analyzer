import io
import streamlit as st
import pandas as pd
from openai import OpenAI

# Load OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Estimate ARV based on comps
def estimate_arv(comps_df):
    comps_df['price_per_sqft'] = comps_df['price'] / comps_df['sqft']
    avg_ppsqft = comps_df['price_per_sqft'].mean()
    subject_arv = avg_ppsqft * comps_df['subject_sqft'].iloc[0]
    return round(subject_arv, 2)

# Estimate rehab based on level
def estimate_rehab(sqft, level):
    rates = {'Light': 20, 'Medium': 35, 'Heavy': 50}
    return sqft * rates.get(level, 35)

# Calculate MAO using standard formula
def calculate_mao(arv, rehab_cost, profit_margin=0.2):
    return round(arv * (1 - profit_margin) - rehab_cost, 2)

# Generate smart investor commentary
def generate_gpt_commentary(arv, mao, rehab):
    prompt = f"""
    Analyze this real estate flip:
    ARV: ${arv}
    Rehab Cost: ${rehab}
    MAO: ${mao}
    Provide a one-paragraph smart investor summary.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Streamlit UI
st.title("🏠 FlipSmart AI – Deal Analyzer")

with st.form("deal_form"):
    address = st.text_input("📍 Property Address")
    subject_sqft = st.number_input("🏡 Property Sqft", 500, 10000, 1500)
    rehab_level = st.selectbox("🔨 Rehab Level", ["Light", "Medium", "Heavy"])
    purchase_price = st.number_input("💰 Purchase Price", 10000, 2000000, 250000)

    st.markdown("### 📊 Comparable Sales")
    comps_data = st.text_area("Enter 3-5 comps (address, price, sqft) as CSV",
        "123 A St,300000,1500\n456 B Rd,320000,1600\n789 C Ave,310000,1550")

    submitted = st.form_submit_button("Analyze Deal")

if submitted:
    comps = pd.read_csv(io.StringIO(comps_data), names=["address", "price", "sqft"])
    comps['subject_sqft'] = subject_sqft

    # Run calculations
    arv = estimate_arv(comps)
    rehab_cost = estimate_rehab(subject_sqft, rehab_level)
    mao = calculate_mao(arv, rehab_cost)

    # Deal verdict
    if purchase_price <= mao:
        verdict = "✅ Great Deal! The purchase price is below your Max Allowable Offer."
    else:
        verdict = "❌ Too Expensive. The purchase price is above your MAO."

    # GPT commentary
    commentary = generate_gpt_commentary(arv, mao, rehab_cost)

    # Display results
    st.success("✅ Deal Analyzed")
    st.metric("Estimated ARV", f"${arv:,.2f}")
    st.metric("Rehab Cost", f"${rehab_cost:,.2f}")
    st.metric("Max Allowable Offer (MAO)", f"${mao:,.2f}")
    st.markdown(f"### {verdict}")
    st.markdown("---")
    st.markdown("**🧠 Deal Summary:**")
    st.text_area("AI Commentary", value=commentary, height=200)
