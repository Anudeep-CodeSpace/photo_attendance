#!/bin/bash

echo "----------------------------------------"
echo " Starting Photo Attendance Backend"
echo " Using uv + FastAPI + Uvicorn"
echo " Enforcing Python 3.10"
echo "----------------------------------------"

# ==================================================
# 1. Ensure Python 3.10 is installed via uv
# ==================================================
if ! uv python list | grep -q "3.10"; then
    echo "📦 Python 3.10.x not found in uv. Installing..."
    uv python install 3.10
else
    echo "✔ Python 3.10.x already installed in uv."
fi


# ==================================================
# 2. Create .venv using Python 3.10 if missing
# ==================================================
if [ ! -d ".venv" ]; then
    echo "⚙️  Creating virtual environment with Python 3.10..."
    uv venv --python 3.10 .venv
fi


# Activate venv
source .venv/bin/activate


# ==================================================
# 3. Validate Python version
# ==================================================
PY_MAJOR=$(python -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" != "3" ] || [ "$PY_MINOR" != "10" ]; then
    echo "❌ Incorrect Python version detected: $(python --version)"
    echo "Expected: Python 3.10.x"
    echo "Recreating venv with Python 3.10..."
    deactivate 2>/dev/null
    rm -rf .venv
    uv venv --python 3.10 .venv
    source .venv/bin/activate
fi

echo "✔ Using Python: $(python --version)"


# ==================================================
# 4. Sync dependencies
# ==================================================
echo "🔧 Syncing dependencies using uv..."
uv sync --active


# ==================================================
# 5. Initialize database if missing
# ==================================================
DB_PATH="app/db/student_details.db"
INIT_SCRIPT="app/db/init_db.py"

if [ ! -f "$DB_PATH" ]; then
    echo "🗄️  Database not found. Initializing..."
    python "$INIT_SCRIPT"
fi


# ==================================================
# 6. Start FastAPI server
# ==================================================
echo "🚀 Starting FastAPI server at http://127.0.0.1:8000"

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo "----------------------------------------"
echo " Server stopped"
echo "----------------------------------------"
