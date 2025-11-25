An intelligent real-time water leakage detection and monitoring system using AI + Smart Home IoT

🚀 Live Deployment
🔗 https://waterleak-ai-g28fbbetprvzufurepo4dd.streamlit.app/

📝 Description
WaterLeak.AI continuously monitors pipelines inside buildings to detect leaks before they cause damage.
It analyzes sensor readings like:

Pressure
Flow Rate
Temperature
Vibration
RPM
Operation Hours
The platform detects unusual patterns → predicts risk → displays alerts instantly.

🎯 Product Highlights
Feature	Benefit
🧠 AI Prediction	Detects hidden leaks early
🏠 Room Mapping	Pipeline blueprint per room
🔴 Risk Alerts	Critical & high-risk warnings
📊 Dashboard	Heatmaps and daily alert trends
🤖 AI Assistant	Gemini-powered insights
🔔 Notifications	Emergency alert banners
🏡 Monitored Rooms
Kitchen • Bathroom • Master Bathroom • Living Room • Laundry • Balcony • Basement
	
🧩 Tech Stack
Layer	Tech
UI	Streamlit, Plotly, HTML+CSS
Backend	FastAPI / Cloud Run
AI Agent	Gemini
Data	BigQuery (planned)
Hosting	Streamlit Cloud (planned)
⚙️ Setup Guide
git clone https://github.com/meharkp7/leakguard-waterleak-agent
cd leakguard-waterleak-agent
pip install -r requirements.txt
streamlit run app.py

🗺️ System Architecture
IoT Sensors → LeakGuard API → Prediction + Analytics → UI
                           ↘ Gemini Agent ↗

🧪 ML Model Output Examples
Field	Meaning
risk_level	low / medium / high / critical
leakage_prob	probability score
leakage_flag	1 = Leak detected, 0 = Safe
👩‍💻 Author

Mehar Kapoor
B.Tech — ECE (AI), IGDTUW
🔗 GitHub: https://github.com/meharkp7

🔗 LinkedIn: (Add your link)

📌 GitHub Topics (Add in repo → Settings → Topics)
streamlit
leak-detection
iot
smart-home
gemini
water-monitoring
ai-ml
cloud-run
plotly
pipeline
