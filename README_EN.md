[中文](README.md) | English

# 📜 AI Novel-to-Script Converter

An intelligent novel-to-script adaptation tool powered by LLMs (DeepSeek / OpenAI / GLM / Kimi / Tongyi Qianwen / Custom). Supports multi-model parallel conversion and comparative scoring. Upload a novel file, automatically detect chapter structure, and generate structured YAML scripts chapter by chapter — complete with scene breakdowns, natural-sounding dialogue, performance direction (tone/action), and screenwriter notes.

## 🎬 Demo

[▶️ Demo Video](demo-video.mp4) (coming soon)

Live demo: see Quick Start below.

## ✨ Key Features

| Feature | Description |
|---|---|
| 📁 Multi-format Parsing | Upload TXT / DOCX / PDF novel files |
| 📖 Smart Chapter Detection | Regex matching for Chinese/English chapter title patterns |
| 🤖 AI Chapter Conversion | LLM-powered conversion of narrative text into structured scripts |
| ⚡ Concurrent Processing | ThreadPoolExecutor handles 3 chapters simultaneously (3x speedup) |
| 📡 Real-time SSE Streaming | Server-Sent Events push conversion progress live |
| ✏️ Revision Support | Regenerate scripts based on user feedback |
| ✅ Schema Validation | Automatic validation of YAML output structure |
| 🔑 Key Verification | Instant API key validation upon saving |
| 🔬 Multi-Model Compare | Run 3 models in parallel, compare scores side-by-side |
| 👥 Character Consistency | Cross-chapter character profile tracking and injection |
| 📋 Adaptation Strategy | Professional adaptation analysis report |
| 📺 Episode Splitting | Auto-split scenes into episodes by target duration |
| ⚡ Conflict Detection | Automatic conflict type and intensity tagging |

## 🏗 Script Output Format

```yaml
scenes:
  - scene_id: 1
    location: "INT - Main Hall - Day"
    chapter: "Chapter 1: The Departure"
    characters_present:
      - name: "Lin Feng"
        role: "Protagonist"
    summary: "Lin Feng enters the main hall for the first time"
    dialogues:
      - speaker: "Lin Feng"
        lines:
          - "I'm here to see the city lord."
        tone: "Calm but determined"
        action: "Stops walking, looks directly at the servant"
    scene_notes: "Opening conflict scene, establishes protagonist's calm demeanor"
```

## 📂 Project Structure

```
novel-to-script/
├── main.py                 # FastAPI backend (SSE streaming + parallel multi-model)
├── converter.py            # Core conversion engine (concurrent + YAML parsing + character injection)
├── chapter_splitter.py     # Automatic chapter detection and splitting
├── character_manager.py    # Character consistency engine (cross-chapter tracking)
├── adaptation_agent.py     # Adaptation agent (strategy/duration/difficulty/conflict detection)
├── llm_client.py           # Multi-provider adapter (DeepSeek/OpenAI/GLM/Kimi/Qwen/custom)
├── prompts.py              # LLM prompt template management
├── schema.py               # Script YAML schema definition and validation
├── file_parser.py          # File parsing (txt/docx/pdf text extraction)
├── requirements.txt        # Python dependencies
├── SCHEMA.md               # YAML Schema design document
├── README.md               # Chinese documentation
├── README_EN.md            # English documentation (this file)
└── frontend/               # React + Vite + TypeScript frontend
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- LLM API Key (from your provider: DeepSeek / OpenAI / GLM / Kimi / Qwen etc.)

### Installation & Running

```bash
# 1. Clone the repository
git clone https://github.com/yyying448/novel-to-script.git
cd novel-to-script

# 2. Create virtual environment and install backend dependencies
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Start the backend
python main.py

# 4. (Optional) Start React frontend — open a second terminal
cd frontend && npm install && npx vite --host

# 5. Open your browser
# Backend only: http://127.0.0.1:8000
# Full frontend: http://localhost:5173
```

### Usage Flow

1. **Configure LLM** — Select provider, enter API key, click verify
2. **Upload Novel** — Drag & drop or paste text (supports txt/docx/pdf)
3. **Preview Chapters** — Confirm chapter detection is correct
4. **Start Conversion** — Click convert, watch real-time progress
5. **View / Revise** — YAML source / visual script / submit feedback for revision

## 🔧 Technical Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend    │────▶│   FastAPI    │────▶│  DeepSeek /   │
│  (React SSE)  │◀────│   Backend    │◀────│  OpenAI etc.  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                    ┌───────┴───────┐
                    │  ThreadPool   │
                    │  (3 workers)  │
                    └───────────────┘
```

- **Backend**: FastAPI + Uvicorn
- **Frontend**: React + Vite + TypeScript + Tailwind CSS
- **AI Engine**: Multi-model support (DeepSeek / OpenAI / GLM / Kimi / Qwen), OpenAI SDK compatible
- **Concurrency**: ThreadPoolExecutor (max_workers=3), SSE streaming progress
- **Timeout Protection**: 120-second LLM call timeout

## 📦 Third-party Dependencies & Original Features

### Third-party Libraries

| Library | Purpose | License |
|---|---|---|
| FastAPI | Web framework | MIT |
| Uvicorn | ASGI server | BSD |
| Jinja2 | Template rendering | BSD |
| OpenAI SDK | LLM API calls (multi-model compatible) | Apache 2.0 |
| PyYAML | YAML parsing & generation | MIT |
| python-multipart | File upload parsing | Apache 2.0 |
| python-docx | Word document parsing | MIT |
| pdfplumber | PDF text extraction | MIT |

### Original Features (Core Code)

| Module | Feature | Description |
|---|---|---|
| `chapter_splitter.py` | Chapter title regex engine | Supports "Chapter X", "第X章" and multiple formats, with token estimation |
| `prompts.py` | Script adaptation prompt engineering | 6 adaptation principles, dialogue naturalization, tone/action generation |
| `schema.py` | Script YAML data structure | 18-field hierarchical schema, validation logic, LLM output error recovery |
| `converter.py` | Concurrent conversion engine | ThreadPoolExecutor scheduling, YAML fault-tolerant parsing, scene ordering |
| `main.py` | SSE streaming + parallel models | Server-Sent Events + asyncio.Queue cross-thread progress, 3-model parallel |
| `character_manager.py` | Character consistency engine | Cross-chapter auto-profiling, injection, relationship inference, deep analysis |
| `adaptation_agent.py` | Adaptation agent | Strategy reports, duration estimation, difficulty tagging, conflict detection |
| `llm_client.py` | Multi-provider adapter | Provider registry + client factory, supports 5 providers + custom endpoints |
| `frontend/` | React SPA | Vite + TypeScript + Tailwind component-based SPA with sidebar navigation |

## 📄 License

MIT License
