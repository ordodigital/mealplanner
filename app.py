import streamlit as st
from openai import OpenAI
import requests
import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="Meal Planner AI", page_icon="👨‍🍳", layout="centered")

# CSS to make Streamlit look like a branded mobile app
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .stButton>button { width: 100%; border-radius: 15px; font-weight: bold; padding: 1rem; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; font-weight: 900; color: #2563eb; }
    .recipe-card { background: white; padding: 20px; border-radius: 20px; border: 1px solid #E2E8F0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 1. ACCESS SECURED KEYS ---
# Streamlit handles these on the server side. Zero exposure to the browser.
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    WEATHER_KEY = st.secrets["WEATHER_API_KEY"]
    UNSPLASH_KEY = st.secrets["UNSPLASH_ACCESS_KEY"]
except Exception:
    st.error("Secrets missing. Please add API keys to Streamlit Secrets dashboard.")
    st.stop()

# --- 2. SIDEBAR / PREFERENCES ---
st.sidebar.image("https://methodshop.com/apps/smartmealplanner/chef-hat-icon.png", width=60)
st.sidebar.title("Preferences")

user_loc = st.sidebar.text_input("Location (City, Zip)", "Raleigh, NC")
house_size = st.sidebar.number_input("Household Size", min_value=1, value=3, step=1)
dietary = st.sidebar.text_area("Dietary Restrictions", placeholder="e.g. Pescatarian, no dairy, no scallops")
favorites = st.sidebar.text_area("Favorite Ingredients/Meals", placeholder="e.g. Salmon, Broccoli, Thai Curry")
temp_unit = st.sidebar.selectbox("Temperature Scale", ["Fahrenheit", "Celsius"])

# Session State for navigation and favorites
if 'tab' not in st.session_state: st.session_state.tab = "Meal Plan"
if 'favs' not in st.session_state: st.session_state.favs = []
if 'plan' not in st.session_state: st.session_state.plan = None

# Navigation Simulation (Bottom Navigation logic)
st.sidebar.divider()
if st.sidebar.button("Log Out"):
    st.session_state.clear()
    st.rerun()

# --- 3. TOP WEATHER WIDGET ---
def get_weather(loc, unit_choice):
    u = 'imperial' if unit_choice == "Fahrenheit" else 'metric'
    sym = '°F' if unit_choice == "Fahrenheit" else '°C'
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={loc}&appid={WEATHER_KEY}&units={u}")
        data = r.json()
        return f"{data['weather'][0]['main']} {round(data['main']['temp'])}{sym}", data['weather'][0]['main']
    except: return "--", "Clear"

weather_str, weather_condition = get_weather(user_loc, temp_unit)

col1, col2 = st.columns([2,1])
with col1:
    st.title("Meal Planner AI")
with col2:
    st.metric(label=user_loc, value=weather_str)

# --- 4. APP TABS ---
nav_cols = st.columns(4)
if nav_cols[0].button("📅 Plan"): st.session_state.tab = "Meal Plan"
if nav_cols[1].button("🛒 List"): st.session_state.tab = "List"
if nav_cols[2].button("⭐ Favs"): st.session_state.tab = "Favorites"
if nav_cols[3].button("⚙️ Setup"): st.session_state.tab = "Setup"

# --- TAB CONTENT: MEAL PLAN ---
if st.session_state.tab == "Meal Plan":
    user_note = st.text_area("Anything special this week?", placeholder="e.g. Busy Tuesday, Anniversary Sunday...")
    
    if st.button("START MEAL PLAN", type="primary"):
        with st.spinner("Chef AI is tailoring your menu..."):
            prompt = f"""
            Family of {house_size}. Location: {user_loc}. Weather: {weather_str}. Date: {datetime.date.today()}.
            Avoid: {dietary}. Favorites: {favorites}. Week context: {user_note}.
            Includes: 5 weekdays dinners, 2 weekend dinners, 2 brunches.
            
            REQUIREMENTS:
            1. Every meal MUST have a PROTEIN and a SIDE.
            2. Real-world shopping units for the combined list (e.g., '1 jar of mayo', '2 heads of broccoli', '1 pack of steaks'). 
            NO cooking measurements like 'teaspoons' in the store list.
            3. Include total prep/cook times and 1-3 emojis.
            
            FORMAT: JSON object
            {{ "meals": [{{ "day": "Monday", "title": "", "emojis": "", "prep": "", "cook": "", "desc": "protein/side", "ingredients": ["item qtyp"] }}], 
              "combined_shopping": ["1 pack Butter", "1 head Garlic"],
              "swaps": ["Alt Meal 1", "Alt Meal 2"] }}
            """
            
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                st.session_state.plan = json.loads(res.choices[0].message.content)
            except Exception as e:
                st.error(f"AI Connection Error: {e}")

    if st.session_state.plan:
        for i, meal in enumerate(st.session_state.plan['meals']):
            st.markdown(f"""
            <div class="recipe-card">
                <span style="color:#2563eb; font-weight:900; font-size:10px; text-transform:uppercase;">{meal['day']}</span>
                <h2 style="margin:0; font-size:1.5rem;">{meal['emojis']} {meal['title']}</h2>
                <p style="color:#64748B; font-style:italic; font-size:14px;">{meal['desc']}</p>
                <div style="font-size:10px; font-weight:bold; color:#94A3B8;">⏱️ PREP: {meal['prep']} | 🔥 COOK: {meal['cook']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Star this Recipe", key=f"star_{i}"):
                if meal['title'] not in st.session_state.favs:
                    st.session_state.favs.append(meal['title'])
                    st.toast(f"Saved {meal['title']}!")

        st.subheader("Quick Recipe Swaps")
        cols = st.columns(len(st.session_state.plan['swaps']))
        for i, swap in enumerate(st.session_state.plan['swaps']):
            cols[i].caption(swap)

# --- TAB CONTENT: SHOPPING LIST ---
elif st.session_state.tab == "List":
    if st.session_state.plan:
        st.header("🛒 Grocery Store List")
        st.info("AI curated for full container sizes (Jars, Packs, Sticks).")
        
        # Combined List
        st.subheader("Combined Items (Store Ready)")
        for item in st.session_state.plan['combined_shopping']:
            st.checkbox(item, key=item)
            
        # Sharing text
        st.divider()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
        share_body = f"Meal Plan Shopping List ({now_str})\n\n" + "\n".join([f"• {x}" for x in st.session_state.plan['combined_shopping']])
        st.text_area("Share this via Email/SMS:", value=share_body, height=200)
    else:
        st.warning("Generate a Meal Plan first!")

# --- TAB CONTENT: FAVORITES ---
elif st.session_state.tab == "Favorites":
    st.header("⭐ Starred Recipes")
    if not st.session_state.favs:
        st.write("No favorites yet.")
    else:
        for f in st.session_state.favs:
            st.success(f)

# --- TAB CONTENT: SETUP ---
elif st.session_state.tab == "Setup":
    st.header("Family Settings")
    st.write("Configure your profile. Changes are applied automatically to your next plan.")
    st.info(f"Signed in as Guest User. Location: {user_loc}")
