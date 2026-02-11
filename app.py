import streamlit as st
import requests
import json
import datetime
import random
import time
from firebase_admin import credentials, firestore, initialize_app, get_app

# --- CONFIGURATION ---
# In a real deployment, put these in st.secrets
GEMINI_API_KEY = "AIzaSyB6QbCSwM8eiwZJzS0qCL8tGZVaTADYAnY"
WEATHER_API_KEY = "0ed98274f6b98d29698832a7e20d2d9e" 
APP_ICON = "https://methodshop.com/apps/smartmealplanner/chef-hat-icon.png"
SPLASH_IMAGE = "https://methodshop.com/apps/smartmealplanner/family-cooking.jpg"

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Meal Planner AI",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM STYLING (Tailwind-ish) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #1e293b;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Components */
    .card {
        background: white;
        padding: 2rem;
        border-radius: 2rem;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.1);
        border: 1px solid #f1f5f9;
        margin-bottom: 1.5rem;
    }
    
    .big-button {
        display: block;
        width: 100%;
        background-color: #ea580c;
        color: white;
        text-align: center;
        padding: 1rem;
        border-radius: 1.5rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        text-decoration: none;
        box-shadow: 0 10px 20px -5px rgba(234, 88, 12, 0.4);
        transition: all 0.2s;
    }
    .big-button:hover {
        background-color: #c2410c;
        transform: translateY(-2px);
    }

    .weather-widget {
        background: #0f172a;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        float: right;
    }

    /* Tabs Styling */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 20px;
        border: none;
        background-color: transparent;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'view' not in st.session_state: st.session_state.view = 'splash'
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'meal_plan' not in st.session_state: st.session_state.meal_plan = None
if 'prefs' not in st.session_state: 
    st.session_state.prefs = {
        'location': 'Raleigh, NC', 
        'size': 4, 
        'diet': '', 
        'unit': 'imperial'
    }

# --- HELPERS ---
def get_weather(location):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&units={st.session_state.prefs['unit']}&appid={WEATHER_API_KEY}"
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            return {
                'temp': round(data['main']['temp']),
                'condition': data['weather'][0]['main'],
                'icon': data['weather'][0]['icon']
            }
    except:
        pass
    return {'temp': '--', 'condition': 'Unknown', 'icon': ''}

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return None

def generate_plan(user_input):
    weather = get_weather(st.session_state.prefs['location'])
    today = datetime.date.today().strftime("%B %d, %Y")
    
    prompt = f"""
    Act as a Michelin-star family meal planner.
    CONTEXT:
    - Date: {today}
    - Weather: {weather['condition']}, {weather['temp']} degrees.
    - Family Size: {st.session_state.prefs['size']} people.
    - Diet: {st.session_state.prefs['diet']}.
    - User Request: {user_input}

    TASK: Create a 7-day plan (5 dinners, 2 weekend dinners, 2 weekend brunches).
    
    REQUIREMENTS:
    1. Real grocery quantities (e.g. "2 lbs chicken" not "2 cups").
    2. Suggest holidays if applicable.
    3. JSON Format.
    
    OUTPUT JSON:
    {{
        "meals": [
            {{
                "day": "Monday",
                "type": "Dinner",
                "name": "Title",
                "description": "Short description...",
                "emojis": "🍗",
                "prep": "15m", "cook": "30m",
                "ingredients": [
                    {{"item": "Chicken Breast", "qty": "2 lbs", "category": "Meat"}}
                ]
            }}
        ],
        "swaps": [
            {{"name": "Quick Tacos", "emojis": "🌮"}}
        ]
    }}
    """
    
    with st.spinner("👨‍🍳 Chef is thinking..."):
        result = call_gemini(prompt)
        if result:
            st.session_state.meal_plan = json.loads(result)
            st.session_state.view = 'planner'
            st.rerun()

# --- VIEWS ---

# 1. SPLASH SCREEN
if st.session_state.view == 'splash':
    st.image(SPLASH_IMAGE, use_column_width=True)
    
    st.markdown(f"""
    <div style="text-align: center; margin-top: -20px; background: white; border-radius: 2rem; padding: 2rem; position: relative; z-index: 10;">
        <img src="{APP_ICON}" style="width: 60px; margin-bottom: 1rem;">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 900;">Meal Planner <span style="color: #ea580c;">AI</span></h1>
        <p style="color: #64748b; font-weight: bold; letter-spacing: 2px; font-size: 0.8rem; text-transform: uppercase;">Eat Better, Planned Simpler.</p>
        <p style="margin-top: 1rem; color: #475569;">Join thousands of families using AI to craft the perfect weekly menu.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sign in with Google", use_container_width=True, type="primary"):
            st.session_state.user_id = "demo_user" # Mock login for now
            st.session_state.view = 'planner'
            st.rerun()
    with col2:
        if st.button("Guest Mode", use_container_width=True):
            st.session_state.user_id = "guest"
            st.session_state.view = 'planner'
            st.rerun()

# 2. MAIN APP
else:
    # -- Header --
    weather = get_weather(st.session_state.prefs['location'])
    
    col_brand, col_weather = st.columns([2, 1])
    with col_brand:
        st.markdown(f"### <img src='{APP_ICON}' width='25' style='vertical-align:middle'> MEAL PLANNER AI", unsafe_allow_html=True)
    with col_weather:
        st.markdown(f"""
        <div class="weather-widget">
            <span>{st.session_state.prefs['location'].split(',')[0].upper()}</span>
            <span>{weather['temp']}°</span>
            <img src="http://openweathermap.org/img/wn/{weather['icon']}.png" width="20">
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")

    # -- Tabs --
    tab_plan, tab_shop, tab_prefs = st.tabs(["📅 Plan", "🛒 Shop", "⚙️ Settings"])

    # -- TAB: PLANNER --
    with tab_plan:
        st.markdown("### Plan Your Week")
        
        # Input Card
        with st.container():
            user_request = st.text_area("What are you craving?", placeholder="e.g. Healthy dinners, taco tuesday...", height=100)
            if st.button("GENERATE MENU ✨", use_container_width=True, type="primary"):
                generate_plan(user_request)

        # Results
        if st.session_state.meal_plan:
            st.success("Menu Generated!")
            
            for meal in st.session_state.meal_plan.get('meals', []):
                with st.expander(f"{meal.get('day')} | {meal.get('emojis')} {meal.get('name')}", expanded=True):
                    st.write(f"_{meal.get('description')}_")
                    cols = st.columns(2)
                    cols[0].caption(f"🕒 Prep: {meal.get('prep')}")
                    cols[1].caption(f"🔥 Cook: {meal.get('cook')}")
                    
                    if st.button(f"Swap {meal.get('day')}", key=f"swap_{meal.get('id', 'x')}"):
                        st.info("Swapping feature coming in next update!")

            st.markdown("### Quick Swaps")
            swaps = st.session_state.meal_plan.get('swaps', [])
            cols = st.columns(len(swaps))
            for idx, swap in enumerate(swaps):
                with cols[idx]:
                    st.markdown(f"**{swap['emojis']}**")
                    st.caption(swap['name'])

    # -- TAB: SHOPPING --
    with tab_shop:
        if not st.session_state.meal_plan:
            st.info("Generate a meal plan first to see your list.")
        else:
            st.markdown("### Grocery List")
            
            # Aggregate ingredients
            shopping_list = {}
            for meal in st.session_state.meal_plan['meals']:
                for ing in meal.get('ingredients', []):
                    cat = ing.get('category', 'Other')
                    if cat not in shopping_list: shopping_list[cat] = []
                    shopping_list[cat].append(f"{ing['qty']} {ing['item']}")
            
            for cat, items in shopping_list.items():
                st.caption(cat.upper())
                for item in items:
                    st.checkbox(item, key=item)
            
            st.markdown("---")
            st.caption("Export")
            
            # Prepare text for copy/email
            list_text = "\n".join([f"{cat}:\n" + "\n".join([f"- {i}" for i in items]) for cat, items in shopping_list.items()])
            
            c1, c2 = st.columns(2)
            if c1.button("📧 Email List"):
                # Mailto link generator
                import urllib.parse
                subject = urllib.parse.quote("My Grocery List")
                body = urllib.parse.quote(list_text)
                st.markdown(f'<a href="mailto:?subject={subject}&body={body}" target="_blank">Click to Open Email Client</a>', unsafe_allow_html=True)
            
            if c2.button("📋 Copy Text"):
                st.code(list_text)

    # -- TAB: SETTINGS --
    with tab_prefs:
        st.markdown("### Preferences")
        
        with st.form("settings_form"):
            loc = st.text_input("Location", value=st.session_state.prefs['location'])
            size = st.number_input("Household Size", value=st.session_state.prefs['size'], min_value=1)
            diet = st.text_input("Dietary Restrictions", value=st.session_state.prefs['diet'])
            unit = st.selectbox("Units", ["imperial", "metric"], index=0 if st.session_state.prefs['unit']=='imperial' else 1)
            
            if st.form_submit_button("Save Changes"):
                st.session_state.prefs = {
                    'location': loc,
                    'size': size,
                    'diet': diet,
                    'unit': unit
                }
                st.success("Settings saved!")
                st.rerun()
        
        if st.button("Log Out", type="secondary"):
            st.session_state.clear()
            st.rerun()
