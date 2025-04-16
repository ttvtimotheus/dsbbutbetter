import os
import json
import time
from loguru import logger
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# In-Memory Cache für Timetables (einfacher Ersatz für Supabase)
TIMETABLE_CACHE = {}

async def init_db() -> None:
    """Initialisiert die Datenbankverbindung (Dummy-Implementation)."""
    logger.info("Verwende In-Memory Cache statt Datenbank")
    return

async def store_timetable(username: str, data: Dict, image_data: bytes, timestamp: str, available_plans=None, available_classes=None) -> bool:
    """
    Speichert einen abgerufenen Stundenplan im In-Memory-Cache.
    
    Args:
        username: Der Benutzername
        data: Die strukturierten Stundenplan-Daten
        image_data: Die Bilddaten des Stundenplans als Base64-String
        timestamp: Der Zeitstempel des Abrufs
        available_plans: Optional, Liste der verfügbaren Pläne
        available_classes: Optional, Liste der verfügbaren Klassen
        
    Returns:
        True bei erfolgreicher Speicherung
    """
    try:
        # Daten vorbereiten
        entry = {
            "data": json.dumps(data),
            "image": image_data if isinstance(image_data, str) else "<binary_data>",  # Nur den String speichern oder Platzhalter für binäre Daten
            "timestamp": timestamp,
            "available_plans": available_plans or [],
            "available_classes": available_classes or []
        }
        
        # Im In-Memory-Cache speichern
        global TIMETABLE_CACHE
        TIMETABLE_CACHE[username] = entry
        
        logger.info(f"Stundenplan erfolgreich im Cache gespeichert für Benutzer {username}")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Stundenplans im Cache: {str(e)}")
        return False
        
async def get_latest_timetable(username: str) -> Optional[Dict]:
    """
    Ruft den zuletzt gespeicherten Stundenplan für einen Benutzer aus dem Cache ab.
    
    Args:
        username: Der Benutzername
        
    Returns:
        Ein Dictionary mit den gespeicherten Daten oder None, wenn kein Plan gefunden wurde
    """
    try:
        global TIMETABLE_CACHE
        if username not in TIMETABLE_CACHE:
            logger.warning(f"Kein Stundenplan im Cache gefunden für Benutzer {username}")
            return None
        
        return TIMETABLE_CACHE[username]
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des letzten Stundenplans aus dem Cache: {str(e)}")
        return None
