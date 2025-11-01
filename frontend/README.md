# Co-Pilot SE - Web Portal Frontend

React TypeScript frontend for Co-Pilot SE multi-cloud architecture generation.

## 🎯 Features

- **Interactive Requirements Form**: Enter architecture requirements with example prompts
- **Real-time Architecture Generation**: See workflow progress with animated loading states
- **Tabbed Results View**:
  - **Architecture Tab**: Mermaid diagram, services table, design rationale, deployment considerations
  - **Cost Analysis Tab**: Cost breakdown by service, cost by category, optimization recommendations
  - **Documentation Tab**: Full HLD document with download/copy functionality
- **Responsive Design**: Works on desktop and mobile with Tailwind CSS
- **Dark Mode Support**: Automatic dark mode based on system preferences

## 🛠️ Technology Stack

- **Framework**: React 18.2.0
- **Language**: TypeScript 5.2.2
- **Build Tool**: Vite 5.0.8
- **Styling**: Tailwind CSS 3.3.6
- **HTTP Client**: Axios 1.6.2 (120s timeout)
- **Diagram Rendering**: Mermaid 10.6.1
- **Markdown**: react-markdown 9.0.1
- **Icons**: lucide-react 0.294.0

## 📦 Installation

```bash
npm install
```

## 🚀 Development

```bash
# Start dev server (localhost:5173)
npm run dev

# Build for production
npm run build
```

## 🔧 Configuration

Create `.env` file:
```env
VITE_API_URL=http://localhost:8000
```

## 📁 Project Structure

```
src/
├── api/client.ts              # API client
├── components/
│   ├── RequirementsForm.tsx   # Input form
│   ├── ArchitectureView.tsx   # Diagram view
│   ├── CostView.tsx           # Cost analysis
│   └── DocumentationView.tsx  # HLD document
├── types.ts                   # TypeScript types
└── App.tsx                    # Main app
```

See full documentation in main project README.
