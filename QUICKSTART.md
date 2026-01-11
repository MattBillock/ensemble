# Ensemble UI - Quick Start Guide

## 🚀 Get the UI Running in 2 Minutes

### Prerequisites
- Python 3.10+ with venv activated
- Node.js 18+ installed
- ANTHROPIC_API_KEY in your `.env` file

### Step 1: Start Backend (Terminal 1)
```bash
cd ~/Development/ai_exploration/ensemble
source venv/bin/activate
cd src/field/ensemble_ui/backend
python main.py
```

Backend will start on `http://localhost:8000`
You should see: `INFO: Uvicorn running on http://0.0.0.0:8000`

### Step 2: Start Frontend (Terminal 2)
```bash
cd ~/Development/ai_exploration/ensemble/src/field/ensemble_ui/frontend
npm install  # Only needed first time
npm run dev
```

Frontend will start on `http://localhost:5173`
You should see: `Local: http://localhost:5173/`

### Step 3: Open Browser
Navigate to: **http://localhost:5173**

---

## 🎯 Using the UI

### Submit a Task
1. Enter task description (e.g., "Create a simple Python function to validate email addresses")
2. Select budget tier:
   - **💰 Economical (0.7x)**: Haiku for most tasks - cheapest
   - **⚖️ Balanced (1.0x)**: Smart mix - recommended
   - **🚀 Full Firepower (2.5x)**: Best models - highest quality
3. Click "Generate Solution"

### Monitor Progress
- **System Online indicator**: Shows if backend is running
- **Active Agents count**: How many agents are currently executing
- **Execution Started card**: Shows task, agent ID, budget tier
- **Real-Time Agent Status**: Live WebSocket updates from agents

---

## 🔧 What's Working Right Now

### ✅ Backend Features
- Budget tier selection (economical/balanced/full_firepower)
- Agent orchestration with Executive Director
- Real-time WebSocket status updates
- 7 API endpoints:
  - POST /api/generate-solution
  - GET /api/status
  - GET /api/available-models
  - GET /api/agents
  - GET /api/agents/{tier}/{name}
  - POST /api/agents/update
  - WebSocket /ws/agent-status

### ✅ Frontend Features
- Budget tier dropdown with descriptions
- Live application status indicator
- Real-time agent status display
- Enhanced progress monitoring
- Responsive design with Tailwind CSS

### ⏸️ Coming Soon
- Agent file editor modal
- Cost tracking display
- Agent hierarchy visualization
- Markdown editor for output
- Multi-task history

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000
# If something is there, kill it
kill -9 <PID>

# Check Python environment
which python  # Should be in venv
pip list | grep anthropic  # Should show anthropic package
```

### Frontend won't start
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check if port 5173 is in use
lsof -i :5173
```

### "WebSocket connection failed"
- Make sure backend is running first
- Check backend terminal for errors
- Try refreshing the page

### "System Online" shows gray/connecting
- Backend might not be running
- Check `http://localhost:8000/api/status` in browser
- Should return JSON with `{"status": "running", ...}`

---

## 📊 Test Tasks to Try

### Simple (use Economical tier)
```
Create a Python function that checks if a number is prime
```

### Medium (use Balanced tier)
```
Create a React component for a user profile card with name, email, and avatar
```

### Complex (use Full Firepower tier)
```
Design and implement a simple REST API for a todo list application with user authentication
```

---

## 🎨 UI Features Demonstrated

1. **Budget Tier Selection**: Choose cost vs. quality tradeoff
2. **Real-time Status**: See when system is online and how many agents are active
3. **Progress Monitoring**: Watch agent execution in real-time
4. **Budget Tier Badge**: See which tier you selected for each task
5. **Visual Feedback**: Loading states, errors, and success indicators

---

## 💡 Pro Tips

### Cost Control
- Start with **Economical** tier for testing
- Use **Balanced** for normal work
- Use **Full Firepower** only for critical/complex tasks

### Monitoring
- Watch the "Active Agents" count - shows current workload
- Real-time status updates via WebSocket
- Check console (F12) for detailed logs

### Multiple Tasks
- You can submit multiple tasks
- Each gets its own agent_id
- Status polling happens automatically

---

## 🔄 Development Workflow

Now that you have a working UI, you can:

1. **Submit tasks via UI** instead of running Python scripts
2. **Monitor progress** in real-time
3. **Test budget tiers** to see cost/quality tradeoffs
4. **Iterate quickly** with live reload (both frontend and backend)

### Making Changes

**Frontend changes**: Vite hot-reloads automatically
**Backend changes**: Restart the backend (Ctrl+C, then `python main.py` again)

---

## 📝 Next Improvements (Your Feedback Needed!)

What would make this UI more useful for you?
- [ ] Agent hierarchy tree view?
- [ ] Cost tracking dashboard?
- [ ] Task history?
- [ ] Agent file editor?
- [ ] Markdown preview for output?
- [ ] Something else?

**Try it out and let me know what's most valuable!**

---

## 🎯 Current State

**Status**: ✅ **DEMOABLE** - Ready for dogfooding!

You can now:
- Submit tasks with budget tier control
- Monitor agent execution in real-time
- See system status at a glance
- Track active agents count

**Perfect for**: Testing the ensemble system through a clean UI instead of CLI scripts.

Enjoy! 🎉
