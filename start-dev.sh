#!/bin/bash

# Farben für die Ausgabe
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting DSB But Better Development Environment${NC}"
echo -e "${BLUE}===================================================${NC}"
echo

# Prüfen der Umgebungsvariablen
if [ ! -f "./backend/.env" ]; then
    echo -e "${BLUE}Backend environment file not found, creating from example...${NC}"
    cp ./backend/.env.example ./backend/.env
    echo -e "${GREEN}Please edit ./backend/.env with your Supabase credentials${NC}"
fi

if [ ! -f "./frontend/.env" ]; then
    echo -e "${BLUE}Frontend environment file not found, creating from example...${NC}"
    cp ./frontend/.env.example ./frontend/.env
fi

# Starten des Backend-Servers
echo -e "${BLUE}Starting Backend Server...${NC}"
echo -e "${BLUE}--------------------------------------------------${NC}"
cd backend

# Erstellen des virtuellen Environments sicherstellen
python -m venv venv 2>/dev/null || python3 -m venv venv 2>/dev/null || echo "Virtual environment already exists"

# Plattformspezifische Aktivierung
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo -e "${RED}Failed to find virtual environment. Creating a new one...${NC}"
    rm -rf venv
    python -m venv venv || python3 -m venv venv
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo -e "${RED}Failed to create virtual environment. Continuing without it...${NC}"
    fi
fi

# Installation der Abhängigkeiten, falls erforderlich
if ! pip list | grep -q fastapi; then
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Backend im Hintergrund starten
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}Backend running at http://localhost:8000${NC}"
echo

# Warten, bis der Backend-Server gestartet ist
sleep 2

# Starten des Frontend-Servers
echo -e "${BLUE}Starting Frontend Server...${NC}"
echo -e "${BLUE}--------------------------------------------------${NC}"
cd ../frontend

# Installation der Abhängigkeiten, falls erforderlich
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing frontend dependencies...${NC}"
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend running at http://localhost:3000${NC}"
echo

# Warten auf Beenden-Signal
echo -e "${GREEN}Development environment is running!${NC}"
echo -e "${GREEN}Press Ctrl+C to stop both servers${NC}"

# Trap für das Beenden beider Prozesse
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

# Warten
wait
