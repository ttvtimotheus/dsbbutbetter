from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import base64
import io
import re
from typing import Dict, List, Optional
import json
import time
from loguru import logger

from services.dsb_service import get_timetable, authenticate_user, get_specific_plan_image
from services.ocr_service import process_ocr
from services.db import store_timetable, get_latest_timetable

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class SpecificPlanRequest(BaseModel):
    username: str
    password: str
    plan_url: str

class TimetableResponse(BaseModel):
    timetable: Dict
    available_plans: List[Dict] = []  # Liste aller verfügbaren Pläne
    available_classes: List[str] = []  # Liste aller verfügbaren Klassen
    last_updated: str
    status: str
    from_cache: bool = False

@router.post("/parse-plan", response_model=TimetableResponse)
async def parse_plan(request: LoginRequest, background_tasks: BackgroundTasks):
    """
    Authentifiziert den Benutzer bei DSBmobile, ruft den Stundenplan ab,
    führt OCR durch und wandelt den Text in eine strukturierte JSON-Tabelle um.
    
    Die Ergebnisse werden in der Datenbank gespeichert.
    """
    try:
        # Protokollierung des Abrufs (ohne Passwörter)
        logger.info(f"Versuche Stundenplan-Abruf für Benutzer: {request.username}")
        
        # Authentifizierung bei DSBmobile
        auth_result = await authenticate_user(request.username, request.password)
        if not auth_result:
            raise HTTPException(status_code=401, detail="Authentifizierung fehlgeschlagen")
        
        # Letzten gespeicherten Stundenplan abrufen
        cached_result = await get_latest_timetable(request.username)
        
        # Stundenplan-Daten abrufen
        logger.info("Authentifizierung erfolgreich. Rufe Stundenplan ab...")
        image_data = await get_timetable(auth_result)
        
        if not image_data:
            # Falls kein neuer Plan gefunden wurde, aber ein Cache existiert, geben wir den zurück
            if cached_result:
                logger.info("Kein neuer Plan gefunden. Verwende Cache.")
                return TimetableResponse(
                    timetable=json.loads(cached_result["data"]),
                    last_updated=cached_result["timestamp"],
                    status="success",
                    from_cache=True
                )
            raise HTTPException(status_code=404, detail="Kein Stundenplan gefunden")
        
        # Alle verfügbaren Pläne aus der get_timetable-Funktion extrahieren
        available_plans = getattr(auth_result, "available_plans", [])
        logger.info(f"Verfügbare Pläne: {len(available_plans)}")
        
        # Verfügbare Klassen aus den Titeln extrahieren
        available_classes = []
        for plan in available_plans:
            plan_title = plan.get('title', '')
            # Klassen im Format MTL01, MTL02, etc. oder MTL 01, MTL 02 extrahieren
            class_matches = re.findall(r'MTL\s*\d+', plan_title)
            available_classes.extend(class_matches)
        
        # Extrahiere zusätzlich Klassen aus den OCR-Ergebnissen, wenn diese verfügbar sind
        if hasattr(auth_result, 'ocr_results') and auth_result.ocr_results:
            # Extrahiere Klasseninformationen, falls vorhanden
            class_names = []
            try:
                # 1. Prüfe, ob bereits Klasseninformationen im Timetable-Objekt vorhanden sind
                if 'class_names' in auth_result.ocr_results and isinstance(auth_result.ocr_results['class_names'], list):
                    class_names = auth_result.ocr_results['class_names']
                    logger.info(f"Klassen direkt aus OCR-Daten übernommen: {class_names}")
                else:
                    # 2. Fallback: Suche nach Klasseninformationen in den Einträgen
                    # Einfache Pattern-Suche nach Klasseninformationen in der Bildüberschrift
                    class_pattern = re.compile(r'\b(\d{1,2}[a-zA-Z]{1,2})\b')
                    mtl_pattern = re.compile(r'MTL\s*\d+', re.IGNORECASE)
                    classes_found = set()

                    for item in auth_result.ocr_results.get('entries', []):
                        text = item.get('text', '')
                        # Traditionelle Klassen (z.B. 10a)
                        standard_matches = class_pattern.findall(text)
                        classes_found.update(standard_matches)
                        
                        # MTL-Klassen (z.B. MTL 02)
                        mtl_matches = mtl_pattern.findall(text)
                        if mtl_matches:
                            normalized_matches = [re.sub(r'\s+', ' ', match).strip() for match in mtl_matches]
                            classes_found.update(normalized_matches)
                    
                    class_names = sorted(list(classes_found))
                    logger.info(f"Gefundene Klassen aus Textanalyse: {class_names}")
            
                # Fallback, wenn keine Klassen gefunden wurden
                if not class_names:
                    logger.info("Keine Klassen gefunden, verwende Fallback-Klassen")
                    class_names = ["MTL 01", "MTL 02"]
            
                available_classes.extend(class_names)
            except Exception as e:
                logger.error(f"Fehler bei der Extraktion von Klasseninformationen: {str(e)}")
        
        # Duplikate entfernen
        available_classes = list(set(available_classes))
        logger.info(f"Gefundene Klassen: {available_classes}")
        
        # OCR-Verarbeitung im Hintergrund starten
        logger.info("Stundenplan gefunden. Starte OCR-Verarbeitung...")
        ocr_result = await process_ocr(image_data)
        
        # Ergebnisse speichern (im Hintergrund)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        background_tasks.add_task(
            store_timetable, 
            request.username, 
            ocr_result, 
            image_data,
            timestamp,
            available_plans,
            available_classes
        )
        
        return TimetableResponse(
            timetable=ocr_result,
            available_plans=available_plans,
            available_classes=available_classes,
            last_updated=timestamp,
            status="success"
        )

    except Exception as e:
        logger.error(f"Fehler beim Abruf des Stundenplans: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Abruf des Stundenplans")

@router.post("/get-specific-plan")
async def get_specific_plan(request: SpecificPlanRequest, background_tasks: BackgroundTasks):
    """Liest einen spezifischen Plan basierend auf der URL"""
    try:
        logger.info(f"Versuche spezifischen Plan für Benutzer {request.username} zu laden: {request.plan_url}")
        
        # Benutzer authentifizieren
        auth_result = await authenticate_user(request.username, request.password)
        if not auth_result:
            logger.error(f"Authentifizierung fehlgeschlagen für Benutzer: {request.username}")
            raise HTTPException(status_code=401, detail="Ungültige Zugangsdaten")
            
        # Spezifischen Plan laden und OCR durchführen
        logger.info(f"Lade Plan von URL: {request.plan_url}")
        image_data = await get_specific_plan_image(auth_result, request.plan_url)
        
        # OCR-Verarbeitung starten
        ocr_result = await process_ocr(image_data)
        
        # Ergebnisse speichern
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        background_tasks.add_task(
            store_timetable, 
            request.username, 
            ocr_result, 
            image_data,
            timestamp
        )
        
        return TimetableResponse(
            timetable=ocr_result,
            last_updated=timestamp,
            status="success"
        )
            
    except HTTPException as e:
        # HTTP-Exceptions weiterleiten
        raise e
    except Exception as e:
        # Alle anderen Fehler protokollieren und eine generische Fehlermeldung ausgeben
        logger.error(f"Fehler beim Abruf des Stundenplans: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Abruf des Stundenplans")

@router.get("/latest", response_model=TimetableResponse)
async def get_latest(username: str):
    """
    Ruft den zuletzt abgerufenen Stundenplan für einen Benutzer ab.
    """
    try:
        result = await get_latest_timetable(username)
        if not result:
            raise HTTPException(status_code=404, detail="Kein Stundenplan für diesen Benutzer gefunden")
            
        return TimetableResponse(
            timetable=json.loads(result["data"]),
            last_updated=result["timestamp"],
            status="success",
            from_cache=True
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Fehler beim Abruf des letzten Stundenplans: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Abruf des letzten Stundenplans")
