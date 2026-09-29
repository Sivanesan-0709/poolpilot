# 🚗 PoolPilot — Urban Commute & Campus Ride-Pooling Network

> **Problem Statement:** *"Urban Commute & Mobility Crisis: Travel More, Waste More"*. Commuters and students face rising travel costs, heavy traffic, overcrowded public transit, safety barriers for women, and vehicular pollution, while millions of half-empty private vehicles crowd the roads.
> 
> **PoolPilot** is a community-driven peer-to-peer ride-pooling and multimodal mobility network with **6-Factor AI matching**, **Dynamic Safety Matching**, **Trusted Circles (WhatsApp Auto-Share)**, **Verified Campus Networks (15% Student Discount)**, **Multimodal Door-to-Door Planning**, and **Real-Time CO₂ & Rupee Impact Tracking**.

---

## 🌟 Highlights & Key Innovations

- ⚡ **6-Factor AI Match Engine**: Matches route corridor overlap (40%) + timing (20%) + detour required (10%) + budget (10%) + safety trust (10%) + driver reliability (10%), featuring 6-bar explainable AI breakdowns and candidate filtering summaries.
- 🛡️ **Dynamic Safety Matching Layer**: Dynamic safety filter checkboxes (Verified ID, Same College/Company, Same Gender, Min Rating slider 3.0–5.0★, Zero Complaints, Emergency Contact on file) with **single-click relaxation suggestions** (e.g. *"Relax rating filter to 4.0★: +2 matches"*).
- 👨‍👩‍👧 **Trusted Circle & Deviation Monitor**: Store up to 5 family/friends contacts, 1-click WhatsApp live tracking link generation (`wa.me`), and automated **200m route deviation** & stopped vehicle alerts.
- 🎓 **Student Commute Network**: Campus email domain verification (`@rec.ac.in`, `@annauniv.edu`, `@iitm.ac.in`), **15% student pool discount**, campus notice boards, and automatic geographic rider clustering within 2.5 km.
- 🗺️ **Smart Commute Multimodal Transit Graph**: Dijkstra multi-criteria routing combining Chennai Metro (Blue & Green lines), Suburban Railway (South & West lines), MTC Buses (19B, 570, 27B, 23C, 70V), walking connectors ($\le 1.2\text{ km}$), and live carpools with 1-click carpool leg booking.
- 🌱 **Personal & College Impact Dashboard**: Monthly breakdowns (CO₂, Rupees, Fuel, Pooled Rides), **College Impact Cascade** with Indian Lakh formatting (*"Your REC cohort saved 1,420 kg CO₂, ₹1.84 Lakhs this month — Ranked #1 in Chennai!"*), and **HTML5 Canvas Social Share Card** export (.PNG).
- ☁️ **Vercel Serverless Ready**: Lightweight base dependencies (<250MB), `/tmp/poolpilot.db` automatic fallback, and HTTP polling fallback for live tracking when WebSockets are unavailable.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Frontend["Frontend Client (Vanilla HTML5 / CSS3 / ES6 + Leaflet + Chart.js)"]
        UI[Single-Page Responsive UI]
        MapEngine[Leaflet OSM Map & Heatmap]
        Speech[Browser Web Speech API]
        Canvas[HTML5 Social Share Card Generator]
    end

    subgraph API["FastAPI Application Layer (app/main.py)"]
        Auth[Auth & Demo Logins]
        Matching[6-Factor AI Matching Engine]
        SafetyLayer[Dynamic Safety Matching & Relaxation]
        TrustedCircle[Trusted Circle & 200m Deviation Monitor]
        CollegeNet[Campus Network & 15% Discount Engine]
        Multimodal[Dijkstra Multimodal Transit Graph]
        Impact[Personal & College Impact Dashboard]
        LiveTracking[WebSocket + HTTP Polling Fallback]
    end

    subgraph AI["Optional Pretrained AI Subsystems (Lazy-Loaded + Strict Fallbacks)"]
        Chronos[Chronos-Bolt-tiny / Prophet Forecasting]
        VoiceParser[Gazetteer Regex Natural Language Parser]
        OCR[EasyOCR Plate Recognition / Regex]
        FaceMatch[DeepFace / Biometric Verification]
        Semantic[sentence-transformers Semantic Place Search]
    end

    subgraph Data["Data & Routing Layer"]
        DB[(SQLite / PostgreSQL Database)]
        OSRM[Public OSRM API / 3s Timeout]
        OfflineRouter[Haversine 1.3x Offline Fallback Router]
        Gazetteer[Chennai Places Gazetteer (45+ Hubs)]
    end

    UI --> API
    MapEngine --> API
    Speech --> API
    API --> Matching
    API --> SafetyLayer
    API --> TrustedCircle
    API --> CollegeNet
    API --> Multimodal
    API --> Impact
    API --> LiveTracking
    API --> AI
    API --> DB
    Matching --> OSRM
    Matching --> OfflineRouter
    Multimodal --> Gazetteer
```

---

## ⚡ 3-Step Quickstart (Runs on Localhost)

### 1. Install Base Dependencies
```bash
pip install -r requirements.txt
```
*(Optional Pretrained AI Models: `pip install -r requirements-ai.txt`)*

### 2. Launch the Application
```bash
python run.py
```
*(The SQLite database auto-creates and seeds with 25 users, 12 driver routes, 7 college pools, 49 demand records, and precomputed road geometry.)*

### 3. Open in Browser
Visit **[http://localhost:8000](http://localhost:8000)** (or the next free port displayed in the console).

---

## 🧪 Verification & Test Suite

### Pytest Unit Tests (33 Tests)
```bash
python -m pytest -v
```
*(Tests cover: 6-factor AI matching, dynamic safety filters, single-click relaxation, trusted circles, WhatsApp token generation, college discounts, Dijkstra multimodal transit routing, impact calculations, and AI fallback hierarchies.)*

### End-to-End Smoke Test (12 Core Modules)
```bash
python smoke_test.py
```
*(Exercises complete lifecycle: Auth, ID verification, ride posting, 6-factor AI matching, dynamic safety matching, WhatsApp circle tracking, college pools, multimodal itineraries, impact dashboard, OTP verification, live tracking, and serverless readiness.)*

---

## 🎭 Stage Demo Personas & Credentials

One-click **"Demo Login"** buttons are provided in the top header bar for zero stage friction:

| Demo Persona | Role | Details |
| :--- | :--- | :--- |
| **Rahul Verma** | Rider | REC Thandalam Engineering Student, ID & College Verified (@rec.ac.in), Trust Score 92 |
| **Priya Sundaram** | Woman Rider | Cognizant Karapakkam (OMR) Techie, Verified Trust Member |
| **Karthik Subramanian** | Driver | TCS Siruseri, Gold Verified (Trust Score 95, 97.5% On-Time), Honda City |
| **Ananya Krishnan** | Woman Driver | Amazon Kandanchavadi, Women-Only Pool Host, Swift |
| **Platform Admin** | Admin | Mobility Ops Manager, Live Impact Heatmap & AI Subsystem Monitor |

---

## 🎬 2-Minute Hackathon Demo Script

1. **Step 1: One-Click Login & Identity Trust**
   - Click `👤 Rahul (Rider)` in the header.
   - Point out the **Trust Score (92/100)**, **Gold/Silver Badge**, and **Verified Campus Domain (`@rec.ac.in`)**.
   - Open the **Trust & Safety** tab to show the **Trusted Circle** (up to 5 contacts) and **Instant Mock ID / Face Verification**.

2. **Step 2: 6-Factor AI Matching & Voice Booking**
   - Switch to the **Find Ride** tab.
   - Click **🎙️ Voice Booking** and say (or type): *"Ride to T Nagar at 8 AM"*. Destination and timing automatically populate.
   - Alternatively, search Pickup: `Navalur Marina Mall (OMR)` and Drop: `Perungudi Toll Gate (OMR)`.
   - Inspect the **Dynamic Safety Filter** (Verified ID, Min Rating 4.0★, Zero Complaints).
   - Click **⚡ Find Matching Rides**.
   - Show the **#1 Ranked Match (100% Score, ⭐ RECOMMENDED MATCH)**:
     - **Candidate Filtering Summary**: *"Filtered out 12 candidates: 10 outside route corridor, 2 women-only filter"*.
     - **6-Bar Explainable AI Breakdown**: Route Overlap (100), Time Compatibility (98), Detour Required (95), Cost Compatibility (90), Safety (95), Driver Reliability (96).
     - **Dynamic Meeting Point**: *"11m walk (~0.1 min) to OMR main road"*.
     - **Pricing Comparison**: *"₹38 pool fare vs ₹140 auto rickshaw (Save ₹102 / 73%!)"*.

3. **Step 3: Dynamic Safety Relaxation (Zero-Match Scenario)**
   - Set Min Driver Rating to `4.9★` and check `Same Gender Only` for male rider looking for female pools.
   - Click **Find Matching Rides** $\to$ `0 Direct Matches`.
   - Show the **Single-Click Relaxation Suggestions**: *"🔓 Relax rating filter to 4.0★: +2 matches"*.
   - Click the relaxation button $\to$ slider auto-adjusts and re-executes search instantly!

4. **Step 4: Student Commute Network (15% Discount)**
   - Click the **College Pools** tab (`15% Off`).
   - Filter by campus: `Rajalakshmi (REC)` or `Anna University`.
   - Highlight active pools (Tambaram, Velachery, Porur, Guindy to REC).
   - Click **Join Campus Pool** $\to$ notice 15% student discount automatically applied.
   - Click **Notice Board** to post/view live student updates (*"Running 5 mins late due to Tambaram railway crossing"*).

5. **Step 5: Smart Commute Multimodal Planner**
   - Click the **Smart Planner** tab (`Metro+Pool`).
   - Origin: `Tambaram Railway Station`, Destination: `T. Nagar Panagal Park`, Priority: `⚡ Fastest`.
   - Click **Generate Door-to-Door Itineraries**.
   - View the top 3 door-to-door multimodal itineraries across **Suburban Train $\to$ Metro Green Line $\to$ Peer Carpool $\to$ Short Walk**.
   - Click **⚡ Book This Carpool Leg** $\to$ seamlessly switches to Find Ride tab with coordinates pre-filled!

6. **Step 6: Live GPS Drive, 200m Deviation & WhatsApp Auto-Share**
   - Book the ride $\to$ get the **4-Digit Pickup OTP (e.g. 3039)**.
   - Open **My Trips** tab.
   - Click **🔗 Share Trip** $\to$ show the 1-click pre-filled WhatsApp share link (`https://wa.me/?text=...`) with live tracking token and read-only status.
   - Click **🚗 Simulate Drive (Demo)** to see real-time vehicle movement.
   - Click **⚠️ Simulate 600m Deviation** $\to$ geospatial deviation engine detects the >200m detour and fires the **Red Deviation Alert Banner** and SOS trigger.

7. **Step 7: Personal & College Impact Dashboard**
   - Switch to **Impact & Admin** tab.
   - Select month: `March 2026`.
   - Show the **College Impact Cascade Banner**: *"Your REC cohort saved 1,420 kg CO₂, ₹1.84 Lakhs this month — Ranked #1 in Chennai!"*.
   - View the **Personal Impact Grid** (52.8 kg CO₂, ₹3,100 saved, 35.2 L fuel saved, 18 rides).
   - Click **📥 Download Share Card (.PNG)** $\to$ draws the dynamic HTML5 Canvas graphic and downloads `poolpilot_impact_card.png` for social sharing!

---

## 🧠 Pretrained AI Models & Deterministic Fallbacks

All AI modules are configured in `app/config.py`, lazy-loaded on demand, strictly enforce a 5.0-second timeout, and seamlessly fall back to deterministic algorithms if missing or slow:

| AI Subsystem | Pretrained Model | Deterministic Fallback Mechanism |
| :--- | :--- | :--- |
| **1. Demand Forecasting** | `Chronos-Bolt-tiny` / Prophet | Historical hourly moving average by Chennai zone |
| **2. Voice Booking** | Browser Web Speech API (native) | Interactive voice prompt + Chennai gazetteer regex parser |
| **3. Vehicle Plate OCR** | `EasyOCR` (English, CPU) | Indian vehicle registration regex format validator (`TN 09 AB 1234`) |
| **4. Face Match** | `DeepFace` (VGG-Face) | Structural biometric face comparison with similarity confidence |
| **5. Semantic Search** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Multi-token weighted keyword gazetteer ranking |

---

## 🚀 Deployment Guide: GitHub & Vercel

PoolPilot is architected with serverless compatibility out of the box (`api/index.py`, `vercel.json`, lightweight base `requirements.txt`).

### Step 1: Initialize & Push to GitHub
```bash
git init
git add .
git commit -m "feat: complete PoolPilot 2.0 urban commute platform"
git branch -M main
git remote add origin https://github.com/<your-username>/poolpilot.git
git push -u origin main
```

### Step 2: Deploy to Vercel
1. Go to [vercel.com/new](https://vercel.com/new) and import your `poolpilot` GitHub repository.
2. Under **Framework Preset**, select **Other**.
3. Under **Environment Variables**, add:
   - `POOLPILOT_SERVERLESS` = `1`
   - `ENABLE_PRETRAINED_MODELS` = `0` (or `1` if using external inference endpoints)
4. Click **Deploy**.

*(In serverless mode, PoolPilot automatically routes the SQLite database to `/tmp/poolpilot.db`, auto-seeds data on cold starts, uses deterministic AI fallbacks for instant response times, and activates HTTP polling fallback for live trip tracking).*

---

## 🔒 Honest Assessment: Real vs. Mocked Components

| Component | Production Implementation | Hackathon Demo Implementation |
| :--- | :--- | :--- |
| **6-Factor AI Matching** | Cloud Distributed Scoring | Real spatial polyline projection + Corridor bounding + 6-factor weight matrix calculation. |
| **Multimodal Transit** | GTFS Feeds & Live Transit APIs | Real Dijkstra multi-criteria graph with Chennai Metro, Suburban Rail, MTC routes, and Carpools. |
| **ID & Face Verification** | DigiLocker / UIDAI Aadhaar API | Realistic client-side upload interface with facial structure similarity scoring & tier upgrade. |
| **UPI Payments** | Razorpay / Cashfree UPI Gateway | Realistic Mock UPI QR code + in-app wallet balance ledger + commission calculation. |
| **WhatsApp Trip Share** | WhatsApp Business Cloud API | Direct `https://wa.me/?text=...` deep-links with unique cryptographic tracking tokens. |
| **Road Routing** | Commercial Routing Engines | Public OSRM API with 3.0s timeout + Haversine 1.3x offline fallback. |
| **Live GPS Simulation** | Mobile GPS Hardware | Real-time WebSocket stream + REST HTTP Polling fallback + Smooth Drive & Deviation buttons. |

---

## 👥 Authors & License

- **Project:** PoolPilot — Urban Commute & Campus Ride-Pooling Network
- **License:** MIT License
