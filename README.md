# 🚀 Project Setup Guide (with `uv`)

This project uses [`uv`](https://docs.astral.sh/uv/) — a fast and modern Python package manager — to handle environment creation, dependency management, and script execution.

---

## 📦 1. Install `uv`

Follow the official installation guide here:  👉 [UV Installation Guide](https://docs.astral.sh/uv/getting-started/installation/) 🔗

---

## 🛠️ 2. Set Up the Virtual Environment & Install Dependencies

Create the virtual environment and install all dependencies in one step:

```bash
uv sync -c --frozen --no-cache
```
---

## 💾 3. Download and Extract the ChromaDB Database
Use the following command to automatically download and set up the ChromaDB vector database:

```bash
uv run download_vector_db.py
```
✅ No manual steps required — the script will handle everything.

---

## ⚙️ 4. Activate the Virtual Environment (optional)
Activating the environment before running the project is option because uv handles that:

```bash
.venv/Scripts/activate    # Windows
# OR
source .venv/bin/activate # macOS/Linux
```

---

## 🚀 5. Run the Project
Launch the app using:
```bash
uv run fastapi dev
```

---