# 🚀 Project Setup Guide

## 📦 1. Install `uv`

Follow the official installation guide for `uv`:

🔗 [UV Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

---

## 🧪 2. Set Up the Virtual Environment

Create a virtual environment and install all dependencies with a single command:

```bash
uv sync --frozen --no-cache
```

This will:

Create a .venv folder (if not already present)

Install all packages listed in pyproject.toml

## ▶️ 3. Run the Project
```bash
uvicorn main:app
```