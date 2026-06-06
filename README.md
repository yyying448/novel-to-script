[English](README_EN.md) | 中文

# 📜 AI 小说转剧本工具

基于大语言模型（DeepSeek / OpenAI / 智谱 GLM / Kimi / 通义千问 / 自定义）的智能小说改编剧本工具，支持多模型并行转换与对比评分。上传小说文件，自动识别章节结构，逐章生成结构化剧本 YAML，包含场景划分、口语化台词、表演指导（语气/动作）和编剧备注。

## 🎬 Demo

[▶️ 演示视频](demo-video.mp4)（待上传）

在线体验：启动后访问 `http://127.0.0.1:8000`

## ✨ 核心功能

| 功能 | 说明 |
|---|---|
| 📁 多格式解析 | 支持上传 TXT / DOCX / PDF 小说文件 |
| 📖 智能章节识别 | 正则匹配"第X章""Chapter X"等中英文标题格式 |
| 🤖 AI 逐章转换 | 调用 LLM API，将叙事文本转为结构化剧本 |
| ⚡ 并发加速 | ThreadPoolExecutor 同时处理 3 章，速度提升 3 倍 |
| 📡 SSE 实时推送 | Server-Sent Events 流式推送转换进度 |
| ✏️ 二次修改 | 根据用户意见重新生成剧本 |
| ✅ Schema 校验 | 自动校验输出的 YAML 结构完整性 |
| 🔑 Key 验证 | 保存 API Key 时即时验证有效性 |

## 🏗 剧本输出格式

```yaml
scenes:
  - scene_id: 1
    location: "内景 - 城主府大殿 - 日"
    characters_present:
      - name: "林风"
        role: "主角"
    summary: "林风首次进入城主府"
    dialogues:
      - speaker: "林风"
        lines:
          - "我找城主有事，麻烦通报一声。"
        tone: "平静但坚定"
        action: "停下脚步，直视侍女"
    scene_notes: "开场冲突场景，建立主角沉着性格"
```

## 📂 项目结构

```
novel-to-script/
├── main.py                 # FastAPI 后端（SSE流式推送+并行多模型）
├── converter.py            # 核心转换引擎（并发+YAML解析+角色注入）
├── chapter_splitter.py     # 章节自动识别与切分
├── character_manager.py    # 角色一致性引擎（跨章节追踪）
├── adaptation_agent.py     # 改编智能体（策略/时长/难度/冲突检测）
├── llm_client.py           # 多模型适配层（DeepSeek/OpenAI/GLM等）
├── prompts.py              # LLM 提示词模板管理
├── schema.py               # 剧本 YAML Schema 定义与校验
├── file_parser.py          # 文件解析（txt/docx/pdf）
├── requirements.txt        # Python 依赖清单
├── SCHEMA.md               # YAML Schema 设计文档
└── frontend/               # React + Vite + TypeScript 前端
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- LLM API Key（从对应厂商平台获取，支持 DeepSeek / OpenAI / 智谱 / Kimi / 千问等）

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/yyying448/novel-to-script.git
cd novel-to-script

# 2. 创建虚拟环境并安装后端依赖
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 启动后端
python main.py

# 4. (可选) 启动 React 前端 —— 打开第二个终端
cd frontend && npm install && npx vite --host

# 5. 打开浏览器
# 仅后端：http://127.0.0.1:8000
# 完整前端：http://localhost:5173
```

### 使用流程

1. **配置 LLM** — 选择厂商，输入 API Key，点击验证
2. **上传小说** — 拖拽文件或粘贴文本（支持 txt/docx/pdf）
3. **预览章节** — 确认章节切分是否正确
4. **开始转换** — 点击按钮，实时查看进度
5. **查看/修改** — YAML 源码 / 可视化剧本 / 输入意见二次生成

## 🔧 技术架构

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Web 前端    │────▶│  FastAPI     │────▶│  DeepSeek /   │
│  (SSE 流式)   │◀────│  后端服务     │◀────│  OpenAI 等    │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                    ┌───────┴───────┐
                    │  ThreadPool   │
                    │  (3 workers)  │
                    └───────────────┘
```

- **后端**：FastAPI + Uvicorn
- **前端**：原生 HTML/CSS/JS（无框架依赖）
- **AI 引擎**：多模型支持（DeepSeek / OpenAI / GLM / Kimi / 千问），兼容 OpenAI SDK
- **并发策略**：ThreadPoolExecutor（max_workers=3），SSE 流式推送进度
- **超时保护**：LLM 调用 120 秒超时，防止挂死

## 📦 第三方依赖与原创功能说明

### 第三方库

| 库 | 用途 | 许可证 |
|---|---|---|
| FastAPI | Web 框架 | MIT |
| Uvicorn | ASGI 服务器 | BSD |
| Jinja2 | 模板渲染 | BSD |
| OpenAI SDK | LLM API 调用（多模型兼容） | Apache 2.0 |
| PyYAML | YAML 解析与生成 | MIT |
| python-multipart | 文件上传解析 | Apache 2.0 |
| python-docx | Word 文档解析 | MIT |
| pdfplumber | PDF 文本提取 | MIT |

### 原创功能（核心代码）

| 模块 | 原创功能 | 说明 |
|---|---|---|
| `chapter_splitter.py` | 中英文章节标题正则匹配引擎 | 支持"第X章""Chapter X""第X节"等多种格式，含 token 估算与超长章节二次切分 |
| `prompts.py` | 剧本改编专用 Prompt 工程 | 设计 6 项改编原则、对话口语化转换策略、tone/action 表演指导生成 |
| `schema.py` | 剧本 YAML 数据结构设计 | 18 个字段的层级 Schema、完整校验逻辑、LLM 输出容错修复 |
| `converter.py` | 并发转换编排引擎 | ThreadPoolExecutor 并发调度、YAML 容错解析（处理 LLM 不规则输出）、场景顺序保持 |
| `main.py` | SSE 流式推送 + 并行多模型 | Server-Sent Events + asyncio.Queue 跨线程推送进度，三模型并行转换 |
| `character_manager.py` | 角色一致性引擎 | 跨章节角色自动建档、注入、关系推断、深层性格分析 |
| `adaptation_agent.py` | 改编智能体 | 改编策略报告、场景时长估算、拍摄难度标签、冲突检测 |
| `llm_client.py` | 多模型适配层 | 厂商注册表+客户端工厂，支持 5 个厂商+自定义接口 |
| `frontend/` | React 前端 | Vite + TypeScript + Tailwind 组件化 SPA，侧边栏导航 |

## 📄 许可证

MIT License
