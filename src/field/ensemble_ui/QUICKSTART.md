# Ensemble UI - Quick Start Guide

## 🚀 Get the UI Running in 2 Minutes

### Prerequisites
- Python 3.10+ with venv activated
- Node.js 18+ installed
- ANTHROPIC_API_KEY in your .env file

### Step 1: Start Backend (Terminal 1)
```bash
cd ~/Development/ai_exploration/ensemble
source venv/bin/activate
cd src/field/ensemble_ui/backend
python main.py
```

Backend starts on http://localhost:8001 (8000 reserved for Firestorm)

### Step 2: Start Frontend (Terminal 2)
```bash
cd ~/Development/ai_exploration/ensemble/src/field/ensemble_ui/frontend
npm install  # Only first time
npm run dev
```

Frontend starts on http://localhost:5173

### Step 3: Open Browser
Navigate to: http://localhost:5173

---

## 🎯 What's Working

### Budget Tier Selection
- 💰 Economical (0.7x) - Haiku for most tasks
- ⚖️ Balanced (1.0x) - Smart mix (recommended)
- 🚀 Full Firepower (2.5x) - Best models

### Progress Monitoring
- System Online indicator
- Active Agents count
- Real-time agent status
- Execution tracking

---

## ✅ Status: DEMOABLE

You can now submit tasks with budget control and monitor execution in real-time!

Enjoy dogfooding! 🎉
