# 🤖 Sidekick — Your AI-Powered Personal Co-Worker

**Sidekick** is an AI-driven assistant built with **LangGraph**, **LangChain**, and **Gradio**.
It combines LLM-based reasoning, evaluation, and browser tools to automate information gathering, evaluation, and task completion in a conversational interface.

---

## 🚀 Features

* 🧠 **LangGraph-based architecture** for modular AI workflows
* 💬 **Interactive chat interface** built with Gradio
* 🔍 **Integrated browser and external tools** for research and automation
* ⚙️ **Structured evaluation** using LangChain’s output parsers
* 🔄 **Async graph execution** for efficient task handling

---

## 🗂️ Project Structure

```
sidekick/
├── app.py               # Gradio frontend & UI logic
├── sidekick.py          # Core AI logic (LangGraph setup)
├── sidekick_tools.py      # Optional extra agent logic
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## 🧰 Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/sidekick.git
cd sidekick
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> 💡 If you encounter dependency issues (especially with NumPy), try:

```bash
pip install numpy==1.26.4
pip install -r requirements.txt --upgrade --force-reinstall
```

---

## 🔑 Environment Setup

Create a `.env` file in the project root and include your API keys:

```bash
OPENAI_API_KEY=your_openai_key_here
SERPER_API_KEY=your_serper_key_here
```

---

## ▶️ Run the App

Start the Gradio interface:

```bash
uv run app.py
```

Then visit the local URL printed in the terminal (usually `http://127.0.0.1:7860/`).

---

## 🧪 Example Interaction

**User:** “Find and summarize today’s tech news.”
**Sidekick:** “Here’s a summary of today’s top 3 tech headlines from trusted sources…”

---

## 🧼 Troubleshooting

If you see import errors like:

```
ImportError: cannot import name 'content' from 'langchain_core.messages'
```

Run:

```bash
pip install -U langchain langgraph langchain-openai
```

If version mismatches persist:

```bash
pip uninstall langchain langchain-core langchain-openai -y
pip install langchain==0.2.14 langchain-openai==0.2.2 langchain-core==0.2.36
```

---

## 🛠️ Tech Stack

* **LangGraph** — Workflow orchestration
* **LangChain** — Agent and tool integration
* **Gradio** — Interactive UI
* **Playwright** — Automated browser actions
* **Python 3.10+**

---

## 📄 License

MIT License © 2025 Saiyudh Mannan

---
