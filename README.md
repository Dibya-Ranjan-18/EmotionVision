# EmotionVision AI 🎭

> **Real-Time Human Emotion & Behavior Analysis Platform**  
> Powered by OpenCV · MediaPipe · FER · Django REST Framework · React (Vite)

---

## ✨ Features

| Feature | Details |
|---|---|
| **Real-Time Emotion Detection** | 7 emotions: Happy, Sad, Angry, Neutral, Fear, Surprise, Disgust |
| **Multi-Face Support** | Tracks up to 5 faces simultaneously |
| **Behavior Analysis** | Blink, smile, eye state, head direction (yaw/pitch) |
| **AI Pipeline** | MediaPipe → Preprocessor → FER → Smoothing |
| **Live Dashboard** | Glassmorphism UI, dark/light theme, Chart.js charts |
| **Timeline** | Auto-scrolling emotion log with timestamps |
| **PDF Export** | Professional report with charts & statistics |
| **MySQL Storage** | 6 normalized tables for sessions, emotions, behavior |

---

## 🗂 Project Structure

```
EmotionDetect/
├── backend/                   # Django REST API
│   ├── ai_pipeline/           # AI detection modules
│   │   ├── detector.py        # MediaPipe face detection
│   │   ├── preprocessor.py    # Image quality & normalisation
│   │   ├── emotion_analyzer.py# FER + temporal smoothing
│   │   ├── behavior_analyzer.py# Blink, smile, head pose
│   │   └── pipeline.py        # Orchestrator
│   ├── apps/
│   │   ├── sessions_app/      # Session lifecycle
│   │   ├── emotion/           # Emotion logs & frame API
│   │   ├── behavior/          # Behavior logs
│   │   ├── analytics/         # Aggregated stats
│   │   └── reports/           # PDF generation
│   ├── emotionvision/         # Django settings & URLs
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/                  # React + Vite
    └── src/
        ├── components/        # 13 reusable components
        ├── pages/             # Dashboard
        ├── context/           # SessionContext (global state)
        ├── hooks/             # useWebcam, useSession
        ├── services/          # Axios API client
        └── styles/            # Design system CSS
```

---

## ⚙️ Prerequisites

- **Python 3.10 – 3.14** (tested on 3.14)
- **Node.js ≥ 18**
- **MySQL 8.0+** running locally
- A **webcam**

---

## 🚀 Installation

### 1. Clone / Open the project

```bash
cd "d:\My Projects\EmotionDetect"
```

### 2. Backend Setup

```bash
cd backend

# Copy environment file and fill in your MySQL credentials
copy .env.example .env
# Edit .env with your DB_USER, DB_PASSWORD, DB_NAME

# Install dependencies
pip install -r requirements.txt

# Create MySQL database (run in MySQL shell)
# CREATE DATABASE emotionvision_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Run migrations
python manage.py makemigrations sessions_app emotion behavior analytics reports
python manage.py migrate

# Start backend
python manage.py runserver
```

Backend runs at: **http://localhost:8000**

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies (if not already done)
node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install

# Start dev server
node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" run dev
```

Frontend runs at: **http://localhost:5173**

---

## 📡 REST API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/start-session/` | Create a new session |
| POST | `/api/stop-session/` | End session, compute analytics |
| POST | `/api/process-frame/` | Submit base64 frame, get AI result |
| GET  | `/api/live-data/` | Get recent timeline & distribution |
| GET  | `/api/session-summary/` | Full session summary |
| GET  | `/api/export-pdf/` | Download PDF report |

---

## 🗃 Database Schema

```sql
sessions       — id, start_time, end_time, status, total_frames, avg_fps
emotion_logs   — id, session, timestamp, emotion, confidence, face_count
face_logs      — id, session, timestamp, face_index, bbox_*, emotion
behavior_logs  — id, session, timestamp, smile, blink, eye_open, head_direction
analytics      — id, session, dominant_emotion, avg_confidence, emotion_distribution
reports        — id, session, file_path, created_at
```

---

## 🧠 AI Pipeline

```
Browser Webcam (JPEG @ 5fps)
    ↓
MediaPipe FaceDetection + FaceMesh
    ↓
ImagePreprocessor (CLAHE normalisation, blur check, padding)
    ↓
FER EmotionAnalyser (PyTorch CNN)
    ↓
Temporal Smoothing (mode of last 5 predictions)
    ↓
BehaviorAnalyser (EAR blink, MAR smile, solvePnP head pose)
    ↓
REST API Response → React Dashboard Update
```

**Confidence threshold:** 60% — below this, emotion is marked "Uncertain"

---

## 🎨 UI Themes

Toggle between **dark** and **light** mode using the ☀️/🌙 button in the navbar.  
Theme preference is saved in `localStorage`.

---

## 📄 PDF Report

Click **Export PDF** (after stopping a session) for a report containing:
- Session info & duration
- Emotion distribution pie chart
- Timeline table (last 30 entries)
- Behavior summary
- AI insights & recommendations

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Bootstrap 5, Chart.js |
| Backend | Python 3.14, Django 6, DRF |
| Database | MySQL 8 (via PyMySQL) |
| AI – Detection | MediaPipe FaceDetection + FaceMesh |
| AI – Emotion | FER (PyTorch-based CNN) |
| AI – Behavior | OpenCV solvePnP, EAR/MAR algorithms |
| PDF | ReportLab + Matplotlib |

---

## 📝 Notes

- **First run:** FER will download pre-trained model weights (~200MB) automatically.
- **Python 3.14:** TensorFlow is not supported; the project uses FER (PyTorch-based) instead.
- **DeepFace alternative:** FER provides equivalent emotion detection accuracy using PyTorch.
