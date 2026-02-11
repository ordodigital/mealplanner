import streamlit as st
from openai import OpenAI
import requests
import datetime
import json

# --- 1. PAGE SETUP (Chef Hat Favicon) ---
st.set_page_config(
    page_title="Meal Planner AI",
    page_icon="https://methodshop.com/apps/smartmealplanner/chef-hat-icon.png",
    layout="centered"
)

# --- 2. CUSTOM CLEAN THEME (High Contrast) ---
st.markdown("""
<style>
    /* Global Styles */
    .stApp { background-color: #FFFFFF; }
    h1, h2, h3 { color: #0F172A !important; font-weight: 800 !important; }
    p { color: #334155 !important; }
    
    /* Header & Weather Styles */
    .header-logo { display: block; margin: 0 auto; width: 80px; }
    .weather-box {
        background: #F8FAFC;
        padding: 10px 20px;
        border-radius: 50px;
        border: 1px solid #E2E8F0;
        text-align: center;
        font-weight: 700;
        color: #2563eb;
    }

    /* Inviting Card Design */
    .meal-card {
        background: white;
        padding: 24px;
        border-radius: 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .day-badge {
        background: #DBEAFE;
        color: #2563EB;
        font-weight: 900;
        font-size: 11px;
        padding: 4px 12px;
        border-radius: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Input Styling */
    .stTextInput>div>div>input, .stTextArea>div>textarea {
        border-radius: 12px !important;
        border: 1px solid #CBD5E1 !important;
    }
    
    /* Primary Action Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        background-color: #2563EB !important;
        color: white !important;
        font-weight: 800 !important;
        height: 3.5rem;
        border: none;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION LOGIC ---
if 'unlocked' not in st.session_state: st.session_state.unlocked = False
if 'current_tab' not in st.session_state: st.session_state.current_tab = "Plan"
if 'meal_plan' not in st.session_state: st.session_state.meal_plan = None
if 'starred' not in st.session_state: st.session_state.starred = []

# API Client
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    WEATHER_KEY = st.secrets["WEATHER_API_KEY"]
    UNSPLASH_KEY = st.secrets["UNSPLASH_ACCESS_KEY"]
except Exception as e:
    st.error("Missing API Keys in Streamlit Secrets Dashboard.")
    st.stop()

# --- 4. VIEW: SPLASH SCREEN ---
if not st.session_state.unlocked:
    st.markdown("<br><br>", unsafe_allow_html=True)
    # Centering via Columns
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image("https://methodshop.com/apps/smartmealplanner/chef-hat-icon.png", width=100)
    
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>Meal Planner AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #2563eb; font-weight: 800; font-style: italic; font-size: 1.2rem; margin-top:-20px;'>Eat Better, Planned Simpler.</p>", unsafe_allow_html=True)
    
    st.image("https://methodshop.com/apps/smartmealplanner/family-cooking.jpg", use_container_width=True)
    
    st.markdown("<p style='text-align: center; font-size: 1.1rem; padding: 10px 40px;'>Join thousands of families using AI to craft the perfect weekly menu based on your tastes and the weather.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("GET STARTED", type="primary"):
        st.session_state.unlocked = True
        st.rerun()
    st.stop()

# --- 5. VIEW: MAIN INTERFACE ---

# 5a. Top Navigation & Weather Header
def get_weather_data(loc):
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={loc}&appid={WEATHER_KEY}&units=imperial")
        data = r.json()
        return f"{round(data['main']['temp'])}°F, {data['weather'][0]['main']}", data['name']
    except: return "--", "Unknown"

# Preferences stored in sidebar for cleanliness
with st.sidebar:
    st.image("https://methodshop.com/apps/smartmealplanner/chef-hat-icon.png", width=60)
    st.header("Preferences")
    p_loc = st.text_input("Family Location", "Raleigh, NC")
    p_size = st.number_input("Household Size", min_value=1, value=3)
    p_diet = st.text_area("Dietary Restrictions", "Pescatarian, no dairy")
    p_favs = st.text_area("Favorite Meals/Ingredients", "Salmon, Broccoli, Tacos")
    p_unit = st.selectbox("Scale", ["Fahrenheit", "Celsius"])
    if st.button("Reset Session"): 
        st.session_state.clear()
        st.rerun()

weather_str, city_name = get_weather_data(p_loc)

# Header Row
head1, head2 = st.columns([2, 1])
with head1:
    st.markdown("<h2 style='margin:0;'>Menu Planner</h2>", unsafe_allow_html=True)
with head2:
    st.markdown(f"<div class='weather-box'>{city_name} • {weather_str}</div>", unsafe_allow_html=True)

# Tabs
tab_p, tab_l, tab_f = st.tabs(["📅 Plan", "🛒 Shopping", "⭐ Favorites"])

# --- TAB: PLANNER ---
with tab_p:
    user_context = st.text_area("What's happening this week?", placeholder="e.g. Late work Tuesday, son loves spicy food, Anniversary Sunday...")
    
    if st.button("CREATE WEEKLY PLAN"):
        with st.spinner("AI Chef is crafting your recipes..."):
            prompt = f"""
            Act as a Michelin-star meal planner for {p_size} people in {p_loc} ({weather_str}).
            Avoid: {p_diet}. Preferences: {p_favs}. User context: {user_context}.
            
            Deliver a week: 5 weeknight dinners, 2 weekend dinners, 2 weekend brunches.
            RULES: 
            1. Every meal must have a Protein and a Side Dish. 
            2. Prep/cook times included. 1-3 Emojis. 
            3. SHOPPING LIST: This is for a grocery store. Convert quantities to "1 jar of mayo", "1 stick of butter", "1 head of lettuce".
            
            JSON FORMAT ONLY:
            {{ "meals": [{{ "day": "Monday", "title": "", "emojis": "", "protein": "", "side": "", "prep": "", "cook": "" }}],
               "shopping": {{ "combined": ["1 jar Mayo"], "pantry": ["Salt", "Olive Oil"] }},
               "swaps": ["Alt Meal 1"] }}
            """
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                st.session_state.meal_plan = json.loads(res.choices[0].message.content)
            except Exception as e:
                st.error(f"AI Connection Failure: {e}")

    if st.session_state.meal_plan:
        for m in st.session_state.meal_plan['meals']:
            # Card Display
            st.markdown(f"""
            <div class="meal-card">
                <span class="day-badge">{m['day']}</span>
                <h2 style='margin-bottom:4px;'>{m['emojis']} {m['title']}</h2>
                <p style='margin-bottom:8px;'><strong>{m['protein']}</strong> with <strong>{m['side']}</strong></p>
                <p style='font-size:11px; font-weight:bold; color:#64748B;'>🕒 {m['prep']} PREP • 🔥 {m['cook']} COOK</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Star {m['title']}", key=m['title']):
                if m['title'] not in st.session_state.starred:
                    st.session_state.starred.append(m['title'])
                    st.toast("Saved to Favorites!")

# --- TAB: SHOPPING ---
with tab_l:
    if st.session_state.meal_plan:
        st.markdown("### Total Grocery List")
        st.caption("AI combined list for your family size")
        for item in st.session_state.meal_plan['shopping']['combined']:
            st.checkbox(item, key=f"shop_{item}")
            
        st.markdown("### Check Your Pantry")
        pantry_list = ", ".join(st.session_state.meal_plan['shopping']['pantry'])
        st.info(pantry_list)
        
        st.divider()
        share_body = f"Meal Plan {datetime.date.today()}:\n\n" + "\n".join(st.session_state.meal_plan['shopping']['combined'])
        st.text_area("SMS Share Text (Timestamp Included)", share_body, height=150)
    else:
        st.info("Start your plan to generate a list.")

# --- TAB: FAVORITES ---
with tab_f:
    st.markdown("### Saved Favorites")
    if not st.session_state.starred:
        st.write("No favorites saved yet.")
    else:
        for f in st.session_state.starred:
            st.success(f)