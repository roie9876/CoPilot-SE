# Quick Start: Knowledge Graph Wizard

## 🚀 Getting Started in 5 Minutes

### Step 1: Ensure Backend is Running

```bash
# Terminal 1
cd /Users/robenhai/CoPilot-SE
source .venv/bin/activate
python -m uvicorn api.server:app --reload --port 8000
```

**Verify**: Visit http://localhost:8000/docs - you should see 4 new `/api/kg/*` endpoints.

---

### Step 2: Start Frontend Dev Server

```bash
# Terminal 2
cd /Users/robenhai/CoPilot-SE/frontend
npm run dev
```

**Verify**: Visit http://localhost:5173 - you should see the React app.

---

### Step 3: Integrate KG Wizard

**Option A: Quick Test (Easiest)**

Replace `main.tsx` content temporarily:

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import KGApp from './KGApp.tsx'  // ← Changed from App.tsx

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <KGApp />
  </StrictMode>,
)
```

**Option B: Add Toggle to Existing App**

Modify `App.tsx` to add a mode switcher:

```typescript
import { useState } from 'react';
import { KGWizard } from './components';
// ... existing imports

function App() {
  const [useKGWizard, setUseKGWizard] = useState(false);

  if (useKGWizard) {
    return <KGWizard onBack={() => setUseKGWizard(false)} />;
  }

  // ... existing App content
  return (
    <div>
      <button 
        onClick={() => setUseKGWizard(true)}
        className="px-4 py-2 bg-blue-600 text-white rounded"
      >
        Try Knowledge Graph Wizard
      </button>
      {/* existing content */}
    </div>
  );
}
```

---

### Step 4: Test the Workflow

1. **Enter Requirements**: "Build an e-commerce platform on Azure for 10,000 users with high availability"
2. **Click "Start Wizard"**: Should call `/api/kg/start` and show first questions
3. **Answer Questions**: Fill in the form and click "Continue"
4. **Watch Progress**: Progress bars should update after each domain
5. **Generate Architecture**: Once ready, click "Generate Architecture"
6. **View Result**: Should display the architecture diagram

---

## 🎨 What You'll See

### Initial Screen
```
┌───────────────────────────────────────┐
│  ✨ Knowledge Graph Architecture      │
│     Wizard                            │
│                                       │
│  Describe your requirements:          │
│  ┌─────────────────────────────────┐ │
│  │ Build an e-commerce...          │ │
│  └─────────────────────────────────┘ │
│                                       │
│        [Start Wizard] →               │
└───────────────────────────────────────┘
```

### Gathering State
```
Progress Bar:
  Identity & Access      ████████░░ 85%
  Runtime Platform       ████░░░░░░ 40%
  ...

Questions:
  1. Which Azure compute service? [Required]
     [ App Service ▼ ]
  
  2. How many users? [Important]
     [ 10000 ]
  
  [Continue →]
```

### Ready State
```
✓ Ready for Architecture Design

All domains at 80%+
[✨ Generate Architecture]
```

---

## 🔧 Environment Setup

Create `frontend/.env` if needed:

```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

This tells the frontend where to find the backend API.

---

## 🐛 Troubleshooting

### "Failed to start KG session"
- **Cause**: Backend not running or wrong port
- **Fix**: Check backend is on port 8000: `lsof -i :8000`

### "CORS error" in console
- **Cause**: Backend CORS not configured for frontend URL
- **Fix**: Check `api/server.py` has `http://localhost:5173` in CORS origins

### Progress bars don't update
- **Cause**: API response format mismatch
- **Fix**: Check backend API returns `domain_confidence` with all 6 keys

### Questions not rendering
- **Cause**: Questions array empty or wrong format
- **Fix**: Check backend returns array of `KGQuestion` objects

---

## 📋 Testing Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can enter requirements text
- [ ] "Start Wizard" creates session
- [ ] First questions appear
- [ ] Can answer questions and submit
- [ ] Progress bars update after submission
- [ ] Conflicts panel shows if conflicts detected
- [ ] Readiness indicator shows correct metrics
- [ ] "Generate Architecture" button appears when ready
- [ ] Architecture displays after generation

---

## 🎯 Example Test Cases

### Test 1: Simple AWS App
**Input**: "Build a simple web app on AWS with 100 users"
**Expected**: 
- Runtime questions (EC2, Lambda, Fargate?)
- Networking questions (VPC, public/private?)
- Data questions (RDS, DynamoDB?)

### Test 2: Azure High Availability
**Input**: "Build an e-commerce platform on Azure for 10,000 users with HA"
**Expected**:
- Identity questions (Azure AD, B2C?)
- Runtime questions (AKS, App Service?)
- Resiliency questions (availability zones, backup?)

### Test 3: Multi-Region GCP
**Input**: "Build a global data pipeline on GCP with multi-region"
**Expected**:
- Data questions (BigQuery, Cloud SQL?)
- Networking questions (VPN, Interconnect?)
- Resiliency questions (cross-region replication?)

---

## 📞 Need Help?

1. Check backend logs: `tail -f api_server.log`
2. Check browser console: F12 → Console tab
3. Check Network tab: F12 → Network → XHR
4. Review docs: `docs/phase5-frontend-complete.md`

---

## ✅ Success Criteria

You've successfully integrated the KG Wizard when:

✓ You can enter requirements and start a session  
✓ Questions appear based on intent detection  
✓ Progress bars update after each submission  
✓ Conflicts are detected and displayed  
✓ Readiness indicator shows accurate metrics  
✓ Architecture generates when ready  
✓ No console errors during workflow  

**Congratulations! You now have a fully functional Knowledge Graph wizard!** 🎉
