import streamlit as st
import openai
import datetime
import json
import base64

# --- CONFIG & BRANDING ---
st.set_page_config(page_title="Meal Planner AI", page_icon="👨‍🍳")

# Branding assets
LOGO_URL = "https://methodshop.com/apps/smartmealplanner/chef-hat-icon.png"
SPLASH_IMG = "https://methodshop.com/apps/smartmealplanner/family-cooking.jpg"

# Secure Key Storage (Replace with your actual key or use Environment Variables)
OPENAI_KEY = "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"

# --- 1. GATEWAY (SPLASH SCREEN) ---
if 'unlocked' not in st.session_state:
    st.session_state.unlocked = False

if not st.session_state.unlocked:
    st.image(LOGO_URL, width=100)
    st.title("Meal Planner AI")
    st.italic("Eat Better, Planned Simpler.")
    st.image(SPLASH_IMG, use_column_width=True)
    st.write("Join thousands of families using AI to craft the perfect weekly menu based on your tastes and the weather.")
    
    st.divider()
    st.subheader("Prove you're human")
    captcha_answer = st.number_input("74 + 1 = ?", step=1)
    
    if st.button("Unlock AI App"):
        if captcha_answer == 75:
            st.session_state.unlocked = True
            st.rerun()
        else:
            st.error("Incorrect answer! 🛑")
    st.stop()

# --- 2. THE MAIN APP INTERFACE ---
st.sidebar.image(LOGO_URL, width=50)
st.sidebar.title("Preferences")

# Preferences inputs
loc = st.sidebar.text_input("Location", "Raleigh, NC")
size = st.sidebar.number_input("Household Size", min_value=1, value=3)
diet = st.sidebar.text_area("Dietary Restrictions", placeholder="e.g. Pescatarian, No scallops, No dairy")
favs = st.sidebar.text_area("Favorite Foods", placeholder="e.g. Tacos, Salmon, Thai Curry")
temp_unit = st.sidebar.radio("Temperature Unit", ["Fahrenheit", "Celsius"])

if st.sidebar.button("Log Out"):
    st.session_state.unlocked = False
    st.rerun()

st.title("Weekly Menu Designer")

user_note = st.text_area("What's happening this week?", placeholder="e.g. Anniversary on Friday, late soccer Tuesday, wife loves sourdough...")

# --- 3. AI LOGIC ---
if st.button("START MEAL PLAN", type="primary"):
    client = openai.OpenAI(api_key=OPENAI_KEY)
    
    prompt = f"""
    Create a weekly meal plan for a household of {size}.
    Location: {loc}. Today: {datetime.date.today()}.
    Dietary: {diet}. Favorites: {favs}. Context: {user_note}.
    
    Requirements:
    1. 5 weekday dinners, 2 weekend dinners, 2 weekend brunches.
    2. MANDATORY: Every meal has a Protein + Side.
    3. Include 1-3 emojis per meal.
    4. SHOPPING LIST: Provide a total combined list using real store quantities (Jars, Packs, Heads, Sticks).
       NO teaspoons or cups in the total store list.
    
    Return the response in this specific format:
    MEAL PLAN:
    [Day]: [Meal Name] [Emojis]
    - Prep/Cook time: 
    - Description: (Note the protein and side)
    
    SHOPPING LIST:
    (Group by Combined Totals, then Per Meal)
    """

    with st.spinner("Chef AI is cooking up your menu..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content
            st.session_state.meal_plan = result
        except Exception as e:
            st.error(f"AI Error: {e}")

# --- 4. DISPLAY RESULTS ---
if 'meal_plan' in st.session_state:
    st.success("Menu Generated!")
    st.write(st.session_state.meal_plan)
    
    # Click-to-SMS sharing
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sms_text = f"My Meal Plan ({now}):\n{st.session_state.meal_plan}"
    st.write(f"Copy the list below to share via SMS or Email.")
    st.text_area("Shareable List", value=sms_text, height=200)
