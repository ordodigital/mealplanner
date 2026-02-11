import streamlit as st
from openai import OpenAI
import requests
import datetime
import json

# --- 1. THEME & MOBILE OPTIMIZATION ---
st.set_page_config(page_title="Meal Planner AI", page_icon="👨‍🍳", layout="centered")

# This forces the app to stay white and hides the techy Streamlit bars/menus
st.markdown("""
    <style>
    /* Clean white background and inviting fonts */
    .stApp { background-color: white; }
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Elegant card styling for recipes */
    .meal-card {
        background: #FFFFFF;
        padding: 20px;
        border-radius: 25px;
        border: 1px solid #F1F5F9;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .protein-badge {
        color: #2563eb;
        font-weight: 900;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Standardizing the big Start Button */
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        border: none;
        height: 3.5rem;
        background-color: #2563eb !important;
        color: white !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Preferences styling */
    .stTextInput>div>div>input, .stTextArea>div>textarea {
        border-radius: 15px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #F8FAFC !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. KEYS & SECRETS ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    WEATHER_KEY = st.secrets["WEATHER_API_KEY"]
    UNSPLASH_KEY = st.secrets["UNSPLASH_ACCESS_KEY"]
except:
    st.error("🔑 API Keys not found. Ensure they are added to Streamlit Cloud Secrets.")
    st.stop()

# --- 3. SESSION STATE ---
if 'unlocked' not in st.session_state: st.session_state.unlocked = False
if 'tab' not in st.session_state: st.session_state.tab = "Meal Plan"
if 'favs' not in st.session_state: st.session_state.favs = []
if 'plan' not in st.session_state: st.session_state.plan = None

# --- 4. SPLASH SCREEN (WHITE & CLEAN) ---
if not st.session_state.unlocked:
    st.image("https://methodshop.com/apps/smartmealplanner/chef-hat-icon.png", width=80)
    st.markdown("<h1 style='text-align: center; margin-top: -20px;'>Meal Planner AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #2563eb; font-style: italic; font-weight: bold;'>Eat Better, Planned Simpler.</p>", unsafe_allow_html=True)
    st.image("https://methodshop.com/apps/smartmealplanner/family-cooking.jpg", use_container_width=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Join thousands of families using AI to craft the perfect weekly menu based on your tastes and the local weather.</p>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown("<p style='text-align: center; font-weight: 900; color: #1E293B;'>74 + 1 = ?</p>", unsafe_allow_html=True)
    ans = st.number_input("Security Check", value=0, step=1, label_visibility="collapsed")
    
    if st.button("Unlock AI App"):
        if ans == 75:
            st.session_state.unlocked = True
            st.rerun()
        else:
            st.error("Try again!")
    st.stop()

# --- 5. MAIN APP UI ---

# WEATHER WIDGET
def get_weather(loc):
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={loc}&appid={WEATHER_KEY}&units=imperial")
        data = r.json()
        temp = round(data['main']['temp'])
        cond = data['weather'][0]['main']
        city = data['name']
        return f"{temp}°F | {cond}", city
    except: return "--", "City"

# APP NAVIGATION (Bottom-Style)
tab_col = st.columns(4)
if tab_col[0].button("📅 Plan"): st.session_state.tab = "Meal Plan"
if tab_col[1].button("🛒 List"): st.session_state.tab = "List"
if tab_col[2].button("⭐ Favs"): st.session_state.tab = "Favorites"
if tab_col[3].button("⚙️ Setup"): st.session_state.tab = "Setup"

# TAB: MEAL PLAN
if st.session_state.tab == "Meal Plan":
    # Sidebar Prefs are actually kept in a clean container at top
    with st.expander("📝 Refine Preferences", expanded=False):
        user_loc = st.text_input("Location", "Raleigh, NC")
        user_size = st.number_input("Household Size", min_value=1, value=3)
        user_diet = st.text_area("Restrictions", placeholder="e.g. no seafood, lactose intolerant")
        user_favs = st.text_area("Favorite Items", placeholder="e.g. Salmon, Sourdough")
    
    weather_str, city_name = get_weather(user_loc)
    st.caption(f"Currently in {city_name}: {weather_str}")

    user_note = st.text_area("What's the vibe this week?", placeholder="e.g. Late gym on Tuesday, Son's birthday Friday...")
    
    if st.button("START MEAL PLAN"):
        with st.spinner("Chef AI is building your menu..."):
            prompt = f"""
            Family of {user_size}. Weather: {weather_str}. Context: {user_note}.
            Restrictions: {user_diet}. Preferences: {user_favs}.
            Includes: 5 weekday dinners, 2 weekend dinners, 2 brunch meals.
            Requirements: Every meal has Protein + Side. Use store quantities for shopping (Jars/Sticks/Packs).
            Output ONLY JSON: 
            {{ "meals": [{{ "day": "Monday", "title": "", "protein": "", "side": "", "prep": "", "cook": "", "emojis": "" }}],
              "store_list": ["1 jar Mayo", "1 pack Butter"], "swaps": ["Alt Meal 1"] }}
            """
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                st.session_state.plan = json.loads(res.choices[0].message.content)
            except Exception as e:
                st.error(f"Connection Failed: {e}")

    if st.session_state.plan:
        for m in st.session_state.plan['meals']:
            # Fetch Image from Unsplash
            img = f"https://source.unsplash.com/800x400/?{m['title'].replace(' ', ',')}"
            st.markdown(f"""
            <div class="meal-card">
                <div class="protein-badge">{m['day']}</div>
                <h3 style="margin-bottom:2px;">{m['emojis']} {m['title']}</h3>
                <p style="color:#64748B; font-size:14px; font-style:italic;">{m['protein']} with a side of {m['side']}</p>
                <div style="font-size:10px; font-weight:bold; color:#94A3B8;">⏱️ {m['prep']} Prep | 🔥 {m['cook']} Cook</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Star {m['title']}", key=m['title']):
                if m['title'] not in st.session_state.favs:
                    st.session_state.favs.append(m['title'])
                    st.toast("Added to Favorites!")

# TAB: LIST
elif st.session_state.tab == "List":
    if st.session_state.plan:
        st.header("🛒 Grocery Store List")
        st.write("Combined items ready for checkout:")
        for item in st.session_state.plan['store_list']:
            st.checkbox(item, key=item)
        
        # Sharing timestamp
        now = datetime.datetime.now().strftime("%I:%M %p, %m/%d")
        share_text = f"Our Shopping List ({now}):\n" + "\n".join(st.session_state.plan['store_list'])
        st.text_area("Click to Copy & Share via SMS", share_text)
    else:
        st.warning("Please generate a meal plan first.")

# TAB: FAVORITES
elif st.session_state.tab == "Favorites":
    st.header("⭐ Saved Favorites")
    if not st.session_state.favs:
        st.write("No recipes saved yet.")
    else:
        for f in st.session_state.favs:
            st.success(f)

# TAB: SETUP
elif st.session_state.tab == "Setup":
    st.header("Preferences & Account")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
