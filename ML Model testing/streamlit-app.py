import streamlit as st
import joblib
import pandas as pd
import warnings

warnings.filterwarnings("ignore")
# ------------------------
# Load the trained model
# ------------------------
model = joblib.load("crop_prediction_lightgbm.pkl")

# ------------------------
# Prediction function
# ------------------------
def predict_crop(village, distt, state, ph, ec, oc, av_p, av_k, zinc, cu, iron, mn):
    input_data = pd.DataFrame([{
        'Village': village,
        'Distt': distt,
        'State': state,
        'pH(1:2)': ph,
        'EC': ec,
        '%OC': oc,
        'Av P(P2O5)': av_p,
        'AvK(K2O)': av_k,
        'Zinc': zinc,
        'Cu': cu,
        'Iron': iron,
        'Mn': mn
    }])
    prediction = model.predict(input_data)
    return prediction[0]

# ------------------------
# Streamlit App Interface
# ------------------------
st.set_page_config(page_title="Soil-based Crop Predictor", layout="centered")
st.title("🌾 AI Crop Recommendation Based on Soil Report")

st.markdown("Fill in the soil details to get the best crop recommendation.")

# Form inputs
with st.form("crop_form"):
    village = st.text_input("Village", "Pipariya")
    distt = st.text_input("District", "narmadapuram")
    state = st.text_input("State", "M.P.")
    
    ph = st.number_input("pH(1:2)", value=7.4)
    ec = st.number_input("EC (dS/m)", value=0.79)
    oc = st.number_input("% Organic Carbon", value=0.78)
    av_p = st.number_input("Available Phosphorus (P2O5)", value=20.00544)
    av_k = st.number_input("Available Potassium (K2O)", value=132.68)
    zinc = st.number_input("Zinc (ppm)", value=4.75)
    cu = st.number_input("Copper (ppm)", value=4.23)
    iron = st.number_input("Iron (ppm)", value=18.11)
    mn = st.number_input("Manganese (ppm)", value=15.27)

    submit = st.form_submit_button("Predict Crop")

# Predict and Display Result
if submit:
    result = predict_crop(village, distt, state, ph, ec, oc, av_p, av_k, zinc, cu, iron, mn)
    st.success(f"🌱 Recommended Crop: **{result}**")
