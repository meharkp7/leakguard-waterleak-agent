import os
import json
from datetime import datetime

import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ========================
# Config & Constants
# ========================

st.set_page_config(
    page_title="WaterLeak.AI – Smart Leak Guardian",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")
if not BACKEND_URL:
    BACKEND_URL = "https://leakguard-api-217279920936.asia-south1.run.app"

PREDICT_URL = f"{BACKEND_URL}/predict"
AGENT_URL = f"{BACKEND_URL}/agent"

ROOMS = [
    "Kitchen",
    "Bathroom",
    "Master Bathroom",
    "Living Room",
    "Laundry",
    "Balcony",
    "Basement",
]

# ========================
# Session State
# ========================

if "current_view" not in st.session_state:
    st.session_state.current_view = "Home"

if "selected_room" not in st.session_state:
    st.session_state.selected_room = "Kitchen"

if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = None

if "sound_enabled" not in st.session_state:
    st.session_state.sound_enabled = True

if "agent_history" not in st.session_state:
    st.session_state.agent_history = []

if "dummy_predictions" not in st.session_state:
    # Generate dummy historical data
    import random
    from datetime import timedelta
    
    predictions = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(50):
        time = base_time + timedelta(hours=i*3.36)
        room = random.choice(ROOMS)
        risk_levels = ["low", "low", "low", "medium", "medium", "high", "critical"]
        risk = random.choice(risk_levels)
        
        if risk == "low":
            prob = random.uniform(0.05, 0.25)
        elif risk == "medium":
            prob = random.uniform(0.25, 0.50)
        elif risk == "high":
            prob = random.uniform(0.50, 0.75)
        else:
            prob = random.uniform(0.75, 0.95)
        
        predictions.append({
            "timestamp": time,
            "room": room,
            "risk_level": risk,
            "probability": prob,
            "pressure": random.uniform(45, 75),
            "flow_rate": random.uniform(60, 100),
            "temperature": random.uniform(70, 100),
            "zone": f"Zone_{random.randint(1, 4)}"
        })
    
    st.session_state.dummy_predictions = predictions

# ========================
# Professional Styling
# ========================

def inject_global_styles():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide Streamlit branding */
    header[data-testid="stHeader"], 
    footer, 
    #MainMenu,
    .stDeployButton {
        visibility: hidden;
        height: 0;
        display: none;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.5);
    }

    /* Main container */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem 1.5rem;
    }

    /* Professional Navigation Bar */
    .pro-navbar {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 1rem 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.8);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }

    .navbar-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .brand-logo {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }

    .brand-text {
        display: flex;
        flex-direction: column;
    }

    .brand-name {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1a202c;
        line-height: 1.2;
    }

    .brand-tagline {
        font-size: 0.75rem;
        color: #718096;
        font-weight: 500;
    }

    /* Professional Cards */
    .pro-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.8);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }

    .pro-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #e2e8f0;
    }

    .card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a202c;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .card-badge {
        font-size: 0.75rem;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
    }

    /* Hero Section */
    .hero-section {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 3rem;
        margin-bottom: 2rem;
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.8);
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        line-height: 1.2;
    }

    .hero-subtitle {
        font-size: 1.25rem;
        color: #4a5568;
        margin-bottom: 2rem;
        line-height: 1.6;
        max-width: 600px;
    }

    .hero-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }

    .stat-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.25rem;
    }

    .stat-label {
        font-size: 0.875rem;
        color: #718096;
        font-weight: 500;
    }

    /* Risk Indicators */
    .risk-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }

    .risk-low {
        background: rgba(72, 187, 120, 0.1);
        color: #22543d;
        border: 1px solid rgba(72, 187, 120, 0.3);
    }

    .risk-medium {
        background: rgba(237, 137, 54, 0.1);
        color: #7c2d12;
        border: 1px solid rgba(237, 137, 54, 0.3);
    }

    .risk-high {
        background: rgba(245, 101, 101, 0.1);
        color: #742a2a;
        border: 1px solid rgba(245, 101, 101, 0.3);
    }

    .risk-critical {
        background: rgba(220, 38, 38, 0.1);
        color: #7f1d1d;
        border: 1px solid rgba(220, 38, 38, 0.3);
        animation: pulse-border 2s infinite;
    }

    @keyframes pulse-border {
        0%, 100% {
            border-color: rgba(220, 38, 38, 0.3);
            box-shadow: 0 0 0 rgba(220, 38, 38, 0);
        }
        50% {
            border-color: rgba(220, 38, 38, 0.6);
            box-shadow: 0 0 20px rgba(220, 38, 38, 0.3);
        }
    }

    /* Room Grid */
    .room-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-top: 1.5rem;
    }

    .room-card-pro {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        padding: 1.5rem;
        border: 2px solid #e2e8f0;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .room-card-pro::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }

    .room-card-pro:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        border-color: #667eea;
    }

    .room-card-pro:hover::before {
        transform: scaleX(1);
    }

    .room-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }

    .room-name {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 0.5rem;
    }

    .room-status {
        font-size: 0.875rem;
        color: #718096;
    }

    /* Agent Chat */
    .chat-container {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        max-height: 500px;
        overflow-y: auto;
        margin-bottom: 1rem;
    }

    .chat-message {
        margin-bottom: 1rem;
        padding: 1rem;
        border-radius: 12px;
        animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .chat-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
    }

    .chat-agent {
        background: #f7fafc;
        color: #1a202c;
        margin-right: 20%;
        border: 1px solid #e2e8f0;
    }

    .chat-label {
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        opacity: 0.8;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }

    /* Form inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* Loading Animation */
    .loading-indicator {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.5rem;
        padding: 2rem;
    }

    .loading-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #667eea;
        animation: bounce 1.4s infinite ease-in-out;
    }

    .loading-dot:nth-child(1) {
        animation-delay: -0.32s;
    }

    .loading-dot:nth-child(2) {
        animation-delay: -0.16s;
    }

    @keyframes bounce {
        0%, 80%, 100% {
            transform: scale(0);
        }
        40% {
            transform: scale(1);
        }
    }

    /* Responsive */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2rem;
        }
        
        .hero-subtitle {
            font-size: 1rem;
        }
        
        .pro-card {
            padding: 1.5rem;
        }
        
        .room-grid {
            grid-template-columns: 1fr;
        }
    }

    /* Pipeline Blueprint Styles */
    .blueprint-container {
        background: #1a202c;
        border-radius: 16px;
        padding: 2rem;
        position: relative;
        min-height: 400px;
        overflow: hidden;
    }

    .blueprint-grid {
        position: relative;
        background-image: 
            linear-gradient(rgba(102, 126, 234, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(102, 126, 234, 0.1) 1px, transparent 1px);
        background-size: 20px 20px;
        height: 100%;
        min-height: 400px;
    }

    .pipe-horizontal {
        position: absolute;
        height: 8px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        border-radius: 4px;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }

    .pipe-vertical {
        position: absolute;
        width: 8px;
        background: linear-gradient(180deg, #3b82f6, #60a5fa);
        border-radius: 4px;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }

    .pipe-node-blueprint {
        position: absolute;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
        transform: translate(-50%, -50%);
        z-index: 10;
        box-shadow: 0 0 20px currentColor;
    }

    .node-inlet {
        background: #10b981;
        color: white;
        border: 3px solid #059669;
    }

    .node-junction {
        background: #f59e0b;
        color: white;
        border: 3px solid #d97706;
    }

    .node-fixture {
        background: #3b82f6;
        color: white;
        border: 3px solid #2563eb;
    }

    .node-leak {
        background: #ef4444;
        color: white;
        border: 3px solid #dc2626;
        animation: leak-pulse 1.5s infinite;
    }

    @keyframes leak-pulse {
        0%, 100% {
            box-shadow: 0 0 20px #ef4444, 0 0 40px #ef4444;
            transform: translate(-50%, -50%) scale(1);
        }
        50% {
            box-shadow: 0 0 30px #ef4444, 0 0 60px #ef4444;
            transform: translate(-50%, -50%) scale(1.1);
        }
    }

    .blueprint-label {
        position: absolute;
        background: rgba(26, 32, 44, 0.9);
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        border: 1px solid rgba(102, 126, 234, 0.3);
        white-space: nowrap;
    }

    /* Chart container */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_global_styles()

# ========================
# Helper Functions
# ========================

def create_timeline_chart():
    """Create a timeline chart of predictions"""
    df = pd.DataFrame(st.session_state.dummy_predictions)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Group by day and risk level
    df['date'] = df['timestamp'].dt.date
    risk_counts = df.groupby(['date', 'risk_level']).size().reset_index(name='count')
    
    return risk_counts

def create_room_risk_chart():
    """Create room-wise risk distribution"""
    df = pd.DataFrame(st.session_state.dummy_predictions)
    room_risks = df.groupby(['room', 'risk_level']).size().reset_index(name='count')
    return room_risks

def get_room_blueprint(room):
    """Generate blueprint configuration for each room"""
    blueprints = {
        "Kitchen": {
            "pipes": [
                {"type": "horizontal", "top": "30%", "left": "10%", "width": "40%"},
                {"type": "vertical", "top": "30%", "left": "50%", "height": "40%"},
                {"type": "horizontal", "top": "70%", "left": "50%", "width": "30%"},
            ],
            "nodes": [
                {"type": "inlet", "top": "30%", "left": "10%", "label": "Main Inlet"},
                {"type": "junction", "top": "30%", "left": "50%", "label": "T-Junction"},
                {"type": "fixture", "top": "70%", "left": "50%", "label": "Sink"},
                {"type": "fixture", "top": "70%", "left": "80%", "label": "Dishwasher"},
                {"type": "leak", "top": "30%", "left": "35%", "label": "⚠️ Leak Detected"},
            ]
        },
        "Bathroom": {
            "pipes": [
                {"type": "vertical", "top": "10%", "left": "30%", "height": "60%"},
                {"type": "horizontal", "top": "40%", "left": "30%", "width": "50%"},
                {"type": "vertical", "top": "40%", "left": "80%", "height": "30%"},
            ],
            "nodes": [
                {"type": "inlet", "top": "10%", "left": "30%", "label": "Main Inlet"},
                {"type": "junction", "top": "40%", "left": "30%", "label": "Junction"},
                {"type": "fixture", "top": "70%", "left": "30%", "label": "Toilet"},
                {"type": "fixture", "top": "40%", "left": "80%", "label": "Shower"},
                {"type": "fixture", "top": "70%", "left": "80%", "label": "Sink"},
            ]
        },
        "Master Bathroom": {
            "pipes": [
                {"type": "horizontal", "top": "20%", "left": "15%", "width": "70%"},
                {"type": "vertical", "top": "20%", "left": "40%", "height": "50%"},
                {"type": "vertical", "top": "20%", "left": "85%", "height": "35%"},
            ],
            "nodes": [
                {"type": "inlet", "top": "20%", "left": "15%", "label": "Main Inlet"},
                {"type": "junction", "top": "20%", "left": "40%", "label": "Splitter"},
                {"type": "junction", "top": "20%", "left": "85%", "label": "T-Joint"},
                {"type": "fixture", "top": "70%", "left": "40%", "label": "Bathtub"},
                {"type": "fixture", "top": "55%", "left": "85%", "label": "Dual Sink"},
                {"type": "leak", "top": "45%", "left": "40%", "label": "⚠️ Minor Leak"},
            ]
        },
        "Living Room": {
            "pipes": [
                {"type": "horizontal", "top": "50%", "left": "20%", "width": "60%"},
            ],
            "nodes": [
                {"type": "inlet", "top": "50%", "left": "20%", "label": "Main Line"},
                {"type": "junction", "top": "50%", "left": "50%", "label": "Pass-through"},
                {"type": "fixture", "top": "50%", "left": "80%", "label": "Radiator"},
            ]
        },
        "Laundry": {
            "pipes": [
                {"type": "vertical", "top": "15%", "left": "40%", "height": "55%"},
                {"type": "horizontal", "top": "40%", "left": "40%", "width": "35%"},
            ],
            "nodes": [
                {"type": "inlet", "top": "15%", "left": "40%", "label": "Main Inlet"},
                {"type": "junction", "top": "40%", "left": "40%", "label": "T-Junction"},
                {"type": "fixture", "top": "70%", "left": "40%", "label": "Utility Sink"},
                {"type": "fixture", "top": "40%", "left": "75%", "label": "Washer"},
                {"type": "leak", "top": "55%", "left": "40%", "label": "⚠️ High Risk"},
            ]
        },
        "Balcony": {
            "pipes": [
                {"type": "horizontal", "top": "35%", "left": "25%", "width": "50%"},
            ],
            "nodes": [
                {"type": "inlet", "top": "35%", "left": "25%", "label": "Main Inlet"},
                {"type": "fixture", "top": "35%", "left": "75%", "label": "Outdoor Tap"},
            ]
        },
        "Basement": {
            "pipes": [
                {"type": "horizontal", "top": "25%", "left": "10%", "width": "80%"},
                {"type": "vertical", "top": "25%", "left": "30%", "height": "45%"},
                {"type": "vertical", "top": "25%", "left": "70%", "height": "45%"},
            ],
            "nodes": [
                {"type": "inlet", "top": "25%", "left": "10%", "label": "Main Supply"},
                {"type": "junction", "top": "25%", "left": "30%", "label": "Branch A"},
                {"type": "junction", "top": "25%", "left": "70%", "label": "Branch B"},
                {"type": "fixture", "top": "70%", "left": "30%", "label": "Boiler"},
                {"type": "fixture", "top": "70%", "left": "70%", "label": "Water Heater"},
                {"type": "fixture", "top": "25%", "left": "90%", "label": "Main Valve"},
            ]
        }
    }
    
    return blueprints.get(room, blueprints["Kitchen"])

# ========================
# Helper Functions
# ========================

def set_view(target: str):
    st.session_state.current_view = target
    st.rerun()

def risk_chip(risk: str) -> str:
    r = (risk or "").lower()
    if r == "low":
        cls = "risk-low"
        icon = "🟢"
    elif r == "medium":
        cls = "risk-medium"
        icon = "🟡"
    elif r == "high":
        cls = "risk-high"
        icon = "🟠"
    else:
        cls = "risk-critical"
        icon = "🔴"
    return f'<span class="risk-indicator {cls}"><span>{icon}</span><span>{risk.title()}</span></span>'

def call_predict_api(payload: dict):
    try:
        with st.spinner("🔍 Analyzing sensor data..."):
            resp = requests.post(PREDICT_URL, json=payload, timeout=15)
            if resp.status_code != 200:
                st.error(f"⚠️ Prediction API error: {resp.status_code}")
                return None
            return resp.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please check if the backend is running.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"🔌 Cannot connect to backend at {BACKEND_URL}. Please verify the URL and ensure the backend is running.")
        return None
    except Exception as e:
        st.error(f"❌ Prediction call failed: {str(e)}")
        return None

def call_agent_api(query: str):
    try:
        with st.spinner("🤖 Agent is thinking..."):
            resp = requests.post(
                AGENT_URL, 
                json={"query": query}, 
                timeout=60,
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code != 200:
                st.error(f"⚠️ Agent API error: {resp.status_code} - {resp.text}")
                return None
            return resp.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Agent request timed out (60s). The query may be too complex.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"🔌 Cannot connect to agent at {AGENT_URL}. Please verify the backend is running.")
        return None
    except Exception as e:
        st.error(f"❌ Agent call failed: {str(e)}")
        return None

# ========================
# Navigation Component
# ========================

def render_navbar():
    st.markdown("""
        <div class="pro-navbar">
            <div class="navbar-brand">
                <div class="brand-logo">💧</div>
                <div class="brand-text">
                    <div class="brand-name">WaterLeak.AI</div>
                    <div class="brand-tagline">Smart Leak Guardian</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
    cols = st.columns(6)
    nav_items = [
        ("Home", "🏠"),
        ("My Home", "🏡"),
        ("Dashboard", "📊"),
        ("Predict", "💧"),
        ("AI Assistant", "🤖"),
        ("Settings", "⚙️")
    ]
    
    for idx, (label, icon) in enumerate(nav_items):
        with cols[idx]:
            if st.button(
                f"{icon} {label}",
                key=f"nav_{label}",
                use_container_width=True,
                type="primary" if st.session_state.current_view == label else "secondary"
            ):
                set_view(label)

# ========================
# View Components
# ========================

def render_home():
    st.markdown("""
        <div class="hero-section">
            <div class="hero-title">Guard Every Water Drop</div>
            <div class="hero-subtitle">
                AI-powered leak detection system that monitors pressure, flow, and vibration 
                in real-time to catch hidden leaks before they become disasters.
            </div>
            <div class="hero-stats">
                <div class="stat-card">
                    <div class="stat-value">7</div>
                    <div class="stat-label">Rooms Monitored</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">24/7</div>
                    <div class="stat-label">Active Monitoring</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">99.2%</div>
                    <div class="stat-label">Detection Accuracy</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="pro-card">
                <div class="card-title">🎯 How It Works</div>
                <p style="color: #4a5568; margin-top: 1rem;">
                    Our ML model analyzes sensor readings from your water system, 
                    identifies patterns, and predicts leak probability with high accuracy.
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="pro-card">
                <div class="card-title">💡 Why It Matters</div>
                <p style="color: #4a5568; margin-top: 1rem;">
                    Early leak detection saves thousands in repairs, prevents water damage, 
                    and reduces waste. Catch problems before they escalate.
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="pro-card">
                <div class="card-title">🤖 AI Assistant</div>
                <p style="color: #4a5568; margin-top: 1rem;">
                    Ask questions in plain language. Get insights about risk zones, 
                    maintenance schedules, and actionable recommendations.
                </p>
            </div>
        """, unsafe_allow_html=True)

def render_my_home():
    # 🚨 Notification logic

    st.markdown("""
        <div class="pro-card">
            <div class="card-header">
                <div class="card-title">🏡 My Smart Home</div>
                <div class="card-badge">7 Rooms Active</div>
            </div>
            <p style="color: #4a5568;">Select a room to view its pipeline blueprint and current risk status.</p>
        </div>
    """, unsafe_allow_html=True)
    
    room_icons = {
        "Kitchen": "🍳",
        "Bathroom": "🚿",
        "Master Bathroom": "🛁",
        "Living Room": "🛋️",
        "Laundry": "🧺",
        "Balcony": "🌿",
        "Basement": "🔧"
    }
    
    cols = st.columns(4)
    for idx, room in enumerate(ROOMS):
        with cols[idx % 4]:
            if st.button(
                f"{room_icons.get(room, '📍')} {room}",
                key=f"room_{room}",
                use_container_width=True
            ):
                st.session_state.selected_room = room
    
    # Selected room blueprint
    selected_room = st.session_state.selected_room
    blueprint = get_room_blueprint(selected_room)
    
    # Count leaks in this room
    room_data = [p for p in st.session_state.dummy_predictions if p['room'] == selected_room]
    critical_count = len([p for p in room_data if p['risk_level'] == 'critical'])
    high_count = len([p for p in room_data if p['risk_level'] == 'high'])
    st.markdown(f"""
        <div class="pro-card" style="margin-top: 2rem;">
            <div class="card-header">
                <div class="card-title">{room_icons.get(selected_room, '📍')} {selected_room} – Live Pipeline Blueprint</div>
                <div class="card-badge">Real-time Monitoring</div>
            </div>
            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                <div class="risk-indicator risk-critical">
                    🔴 {critical_count} Critical Alerts (7d)
                </div>
                <div class="risk-indicator risk-high">
                    🟠 {high_count} High Risk Events (7d)
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    blueprint_css = """
    <style>
    .blueprint-container {
        background: #1a202c;
        border-radius: 16px;
        padding: 2rem;
        position: relative;
        min-height: 400px;
        overflow: hidden;
    }
    .blueprint-grid {
        position: relative;
        background-image:
            linear-gradient(rgba(102, 126, 234, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(102, 126, 234, 0.1) 1px, transparent 1px);
        background-size: 20px 20px;
        height: 100%;
        min-height: 400px;
    }
    .pipe-horizontal {
        position: absolute;
        height: 8px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        border-radius: 4px;
        box-shadow: 0 0 20px rgba(59,130,246,0.5);
    }
    .pipe-vertical {
        position: absolute;
        width: 8px;
        background: linear-gradient(180deg, #3b82f6, #60a5fa);
        border-radius: 4px;
        box-shadow: 0 0 20px rgba(59,130,246,0.5);
    }
    .pipe-node-blueprint {
        position: absolute;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:14px;
        font-weight:bold;
        transform:translate(-50%,-50%);
        z-index:10;
        box-shadow:0 0 20px currentColor;
    }
    .node-inlet {
        background:#10b981; color:white; border:3px solid #059669;
    }
    .node-junction {
        background:#f59e0b; color:white; border:3px solid #d97706;
    }
    .node-fixture {
        background:#3b82f6; color:white; border:3px solid #2563eb;
    }
    .node-leak {
        background:#ef4444; color:white; border:3px solid #dc2626;
        animation: leak-pulse 1.5s infinite;
    }
    @keyframes leak-pulse {
        0%,100% { box-shadow: 0 0 20px #ef4444; transform: translate(-50%,-50%) scale(1); }
        50% { box-shadow: 0 0 60px #ef4444; transform: translate(-50%,-50%) scale(1.15); }
    }
    .blueprint-label {
        position:absolute;
        background:rgba(26,32,44,0.9);
        color:white;
        padding:2px 6px;
        border-radius:6px;
        font-size:10px;
        border:1px solid rgba(102,126,234,0.3);
        white-space:nowrap;
    }
    </style>
    """

    blueprint_html = blueprint_css + '<div class="blueprint-container"><div class="blueprint-grid">'

    for pipe in blueprint["pipes"]:
        if pipe["type"] == "horizontal":
            blueprint_html += f'''
            <div class="pipe-horizontal" style="top:{pipe['top']}; left:{pipe['left']}; width:{pipe['width']};"></div>'''
        else:
            blueprint_html += f'''
            <div class="pipe-vertical" style="top:{pipe['top']}; left:{pipe['left']}; height:{pipe['height']};"></div>'''

    for node in blueprint["nodes"]:
        blueprint_html += f'''
        <div class="pipe-node-blueprint node-{node['type']}" style="top:{node['top']}; left:{node['left']};">
            {node['type'][0].upper()}
        </div>
        <div class="blueprint-label" style="top: calc({node['top']} + 18px); left:{node['left']}; transform:translateX(-50%);">
            {node['label']}
        </div>
        '''

    blueprint_html += '</div></div>'

    st.components.v1.html(blueprint_html, height=700, scrolling=True)
    
    # Legend
    st.markdown("""
        <div class="pro-card" style="margin-top: 1.5rem;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div class="pipe-node-blueprint node-inlet" style="position: static; transform: none;">I</div>
                    <span style="color: #4a5568;">Main Water Inlet</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div class="pipe-node-blueprint node-junction" style="position: static; transform: none;">J</div>
                    <span style="color: #4a5568;">Junction / T-Joint</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div class="pipe-node-blueprint node-fixture" style="position: static; transform: none;">F</div>
                    <span style="color: #4a5568;">Fixture / Outlet</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div class="pipe-node-blueprint node-leak" style="position: static; transform: none;">L</div>
                    <span style="color: #4a5568;">⚠️ Leak Detection Point</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_dashboard():
    st.markdown("""
        <div class="pro-card">
            <div class="card-header">
                <div class="card-title">📊 Leak Overview Dashboard</div>
                <div class="card-badge">Live Analytics</div>
            </div>
            <p style="color: #4a5568;">Interactive monitoring using historical prediction data</p>
        </div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame(st.session_state.dummy_predictions)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    risk_counts = df['risk_level'].value_counts()
    daily_risk = df.groupby('date').size().reset_index(name='events')
    heatmap_df = df.groupby(['date', 'room']).size().reset_index(name='count')
    heatmap_pivot = heatmap_df.pivot(index='room', columns='date', values='count').fillna(0)

    fig_pie = go.Figure(data=[
        go.Pie(labels=risk_counts.index, values=risk_counts.values, hole=0.4)
    ])
    fig_pie.update_layout(title="Risk Level Distribution (7 Days)")

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=daily_risk['date'], y=daily_risk['events'], mode='lines+markers'
    ))
    fig_line.update_layout(title="Leakage Alerts Over Time")

    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=list(heatmap_pivot.columns),
        y=list(heatmap_pivot.index),
        hoverongaps=False
    ))
    fig_heatmap.update_layout(title="Room vs Date – Risk Heatmap")

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_pie, use_container_width=True)
    with c2:
        st.plotly_chart(fig_line, use_container_width=True)

    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.markdown("""
        <div class="pro-card" style="margin-top: 1.5rem;">
            <div class="card-title">🤖 AI Insight</div>
            <p style="color: #4a5568;">Ask the agent to analyze the recent trends</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Get AI Summary", use_container_width=True):
        resp = call_agent_api("Give a short analysis report of last 7 days leak prediction data.")
        if resp and "answer" in resp:
            st.success("AI Analysis Ready!")
            st.markdown(f"""
                <div class="pro-card">
                    <p style="color:#1a202c; line-height:1.6;">
                        {resp['answer']}
                    </p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Agent backend not reachable right now.")

def render_prediction():
    st.components.v1.html("""
        <div class="pro-card">
            <div class="card-header">
                <div class="card-title">💧 Leak Prediction System</div>
                <div class="card-badge">ML Powered</div>
            </div>
            <p style="color: #4a5568;">Enter sensor readings to analyze leak probability</p>
        </div>
    """, height=500, scrolling=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("prediction_form", clear_on_submit=False):
            st.subheader("📊 Sensor Parameters")
            
            c1, c2, c3 = st.columns(3)
            
            with c1:
                pressure = st.number_input("💨 Pressure (PSI)", value=55.0, min_value=0.0, max_value=200.0)
                vibration = st.number_input("📳 Vibration (Hz)", value=2.0, min_value=0.0, max_value=10.0)
                latitude = st.number_input("🌍 Latitude", value=28.6, format="%.4f")
                zone = st.text_input("🗺️ Zone", value="Zone_1")
            
            with c2:
                flow_rate = st.number_input("🌊 Flow Rate (L/min)", value=80.0, min_value=0.0, max_value=500.0)
                rpm = st.number_input("⚙️ RPM", value=1800.0, min_value=0.0, max_value=5000.0)
                longitude = st.number_input("🌍 Longitude", value=77.2, format="%.4f")
                block = st.text_input("🏗️ Block", value="Block_2")
            
            with c3:
                temperature = st.number_input("🌡️ Temperature (°F)", value=90.0, min_value=0.0, max_value=200.0)
                op_hours = st.number_input("⏱️ Operational Hours", value=4000.0, min_value=0.0, max_value=50000.0)
                pipe = st.text_input("🔧 Pipe ID", value="Pipe_1")
                location_code = st.text_input("📍 Location Code", value="LG-77X")
            
            submitted = st.form_submit_button("🔍 Analyze Leak Risk", use_container_width=True)
        
        if submitted:
            payload = {
                "Pressure": pressure,
                "Flow_Rate": flow_rate,
                "Temperature": temperature,
                "Vibration": vibration,
                "RPM": rpm,
                "Operational_Hours": op_hours,
                "Latitude": latitude,
                "Longitude": longitude,
                "Zone": zone,
                "Block": block,
                "Pipe": pipe,
                "Location_Code": location_code,
            }
            
            result = call_predict_api(payload)
            
            if result:
                st.session_state.last_prediction = result
                risk = result.get("risk_level", "critical")
                prob = result.get("leakage_prob", 1.0)
                flag = result.get("leakage_flag", 1)
                
                if risk.lower() == "critical":
                    st.error("🚨 CRITICAL RISK DETECTED! Immediate inspection required.")
                elif risk.lower() == "high":
                    st.warning("⚠️ High risk detected. Schedule inspection soon.")
                else:
                    st.success("✅ System appears normal.")
                
                st.markdown(f"""
                    <div class="pro-card">
                        <div class="card-title">📊 Analysis Results</div>
                        <div style="margin-top: 1.5rem;">
                            <div style="margin-bottom: 1.5rem;">
                                <strong>Risk Assessment:</strong><br/>
                                {risk_chip(risk)}
                            </div>
                            <div style="margin-bottom: 1.5rem;">
                                <strong>Leak Probability:</strong><br/>
                                <span style="font-size: 2rem; font-weight: 700; color: #667eea;">
                                    {prob:.2%}
                                </span>
                            </div>
                            <div>
                                <strong>Prediction:</strong><br/>
                                <span style="color: {'#dc2626' if flag == 1 else '#16a34a'}; font-weight: 600;">
                                    {'🔴 Leak Detected' if flag == 1 else '🟢 No Leak Detected'}
                                </span>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="pro-card">
                <div class="card-title">💡 Tips</div>
                <ul style="color: #4a5568; margin-top: 1rem; line-height: 1.8;">
                    <li>Keep sensor values within typical operating ranges</li>
                    <li>Higher pressure + temperature often indicates stress</li>
                    <li>Unusual vibration patterns may signal issues</li>
                    <li>Use specific Zone/Pipe labels for better tracking</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

def render_agent():
    st.markdown("""
        <div class="pro-card">
            <div class="card-header">
                <div class="card-title">🤖 AI Assistant</div>
                <div class="card-badge">Gemini Powered</div>
            </div>
            <p style="color: #4a5568;">Ask questions about your leak detection system in natural language</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display chat history
    if st.session_state.agent_history:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.agent_history:
            role = msg["role"]
            content = msg["content"]
            css_class = "chat-user" if role == "user" else "chat-agent"
            label = "You" if role == "user" else "AI Assistant"
            
            st.markdown(f"""
                <div class="chat-message {css_class}">
                    <div class="chat-label">{label}</div>
                    <div>{content}</div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Query input
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_area(
            "Ask your question:",
            placeholder="e.g., Which zones have the highest risk? What should I inspect first?",
            height=100,
            label_visibility="collapsed"
        )
    
    with col2:
        st.write("")
        st.write("")
        if st.button("💬 Send", use_container_width=True, type="primary"):
            if query.strip():
                # Add user message to history
                st.session_state.agent_history.append({
                    "role": "user",
                    "content": query
                })
                
                # Call agent API
                resp = call_agent_api(query)
                
                if resp and "answer" in resp:
                    # Add agent response to history
                    st.session_state.agent_history.append({
                        "role": "agent",
                        "content": resp["answer"]
                    })
                    st.rerun()
                else:
                    st.session_state.agent_history.append({
                        "role": "agent",
                        "content": "⚠️ I'm having trouble connecting to the backend. Please check if the agent service is running."
                    })
                    st.rerun()
            else:
                st.warning("Please enter a question first.")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.agent_history = []
        st.rerun()
    
    # Example questions
    st.markdown("""
        <div class="pro-card" style="margin-top: 2rem;">
            <div class="card-title">💡 Example Questions</div>
            <div style="margin-top: 1rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 0.75rem;">
                <div style="padding: 0.75rem; background: #f7fafc; border-radius: 8px; font-size: 0.875rem; color: #4a5568;">
                    "Which zones are at highest risk?"
                </div>
                <div style="padding: 0.75rem; background: #f7fafc; border-radius: 8px; font-size: 0.875rem; color: #4a5568;">
                    "What maintenance should I prioritize?"
                </div>
                <div style="padding: 0.75rem; background: #f7fafc; border-radius: 8px; font-size: 0.875rem; color: #4a5568;">
                    "Summarize leaks from the last week"
                </div>
                <div style="padding: 0.75rem; background: #f7fafc; border-radius: 8px; font-size: 0.875rem; color: #4a5568;">
                    "What patterns do you see in the data?"
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_settings():
    st.markdown("""
        <div class="pro-card">
            <div class="card-header">
                <div class="card-title">⚙️ Settings & Configuration</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="pro-card">
                <div class="card-title">🏠 Home Information</div>
            </div>
        """, unsafe_allow_html=True)
        
        home_name = st.text_input("Home Nickname", value="My Smart Home")
        owner_name = st.text_input("Owner Name", value="Mehar")
        
        st.markdown("""
            <div class="pro-card">
                <div class="card-title">🔔 Notifications</div>
            </div>
        """, unsafe_allow_html=True)
        
        sound_enabled = st.checkbox(
            "Enable sound alerts for critical leaks",
            value=st.session_state.sound_enabled
        )
        st.session_state.sound_enabled = sound_enabled
        
        email_alerts = st.checkbox("Enable email notifications", value=True)
        sms_alerts = st.checkbox("Enable SMS alerts", value=False)
    
    with col2:
        st.markdown("""
            <div class="pro-card">
                <div class="card-title">🔧 System Configuration</div>
                <div style="margin-top: 1rem; color: #4a5568; line-height: 1.8;">
                    <strong>Backend URL:</strong><br/>
                    <code style="background: #f7fafc; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.875rem;">
                        {BACKEND_URL}
                    </code>
                    <br/><br/>
                    <strong>Model:</strong> Trained leak risk classifier<br/>
                    <strong>Agent:</strong> Gemini-powered AI assistant<br/>
                    <strong>Storage:</strong> BigQuery
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div class="pro-card">
                <div class="card-title">ℹ️ About</div>
                <div style="margin-top: 1rem; color: #4a5568; line-height: 1.8;">
                    <strong>Version:</strong> 2.0.0<br/>
                    <strong>Last Updated:</strong> November 2024<br/>
                    <strong>Status:</strong> <span style="color: #16a34a;">● Online</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# ========================
# Main App
# ========================

def main():
    render_navbar()
    
    view = st.session_state.current_view
    
    if view == "Home":
        render_home()
    elif view == "My Home":
        render_my_home()
    elif view == "Dashboard":
        render_dashboard()
    elif view == "Predict":
        render_prediction()
    elif view == "AI Assistant":
        render_agent()
    elif view == "Settings":
        render_settings()
    else:
        render_home()

if __name__ == "__main__":
    main()