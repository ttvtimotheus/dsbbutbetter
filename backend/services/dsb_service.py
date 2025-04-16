import pydsb
import asyncio
import httpx
from loguru import logger
from typing import Dict, List, Optional, Any
import io
import base64
import requests
from urllib.parse import urlparse

async def authenticate_user(username: str, password: str) -> Optional[Any]:
    """
    Authentifiziert einen Benutzer bei DSBmobile.
    
    Args:
        username: DSBmobile Benutzername
        password: DSBmobile Passwort
        
    Returns:
        Das DSB-Objekt bei erfolgreicher Authentifizierung, None sonst
    """
    try:
        # PyDSB initialisieren (mit Version 2.3.0)
        dsb_client = pydsb.PyDSB(username, password)
        
        # Da pydsb keine native async-Unterstützung hat, führen wir den Aufruf in einem ThreadPool aus
        loop = asyncio.get_event_loop()
        
        # Wir versuchen, Nachrichten abzurufen, um zu prüfen, ob die Authentifizierung erfolgreich war
        try:
            # Testen der Verbindung durch Abruf der Pläne
            await loop.run_in_executor(None, dsb_client.get_plans)
            logger.info(f"Erfolgreiche Authentifizierung für Benutzer {username}")
            return dsb_client
        except Exception as conn_err:
            logger.warning(f"Authentifizierung fehlgeschlagen für Benutzer {username}: {str(conn_err)}")
            return None
    except Exception as e:
        logger.error(f"Fehler bei der Authentifizierung: {str(e)}")
        return None

async def get_specific_plan_image(auth_client: Any, plan_url: str) -> bytes:
    """Ruft einen spezifischen Stundenplan anhand der URL ab"""
    try:
        logger.info(f"Lade spezifischen Plan: {plan_url}")
        
        # Direkt die URL verwenden, um den Plan zu laden
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.get(plan_url, verify=False)
        )
        
        if response.status_code != 200:
            logger.error(f"Fehler beim Abruf des Plans: HTTP {response.status_code}")
            raise Exception(f"HTTP-Fehler beim Abruf des Plans: {response.status_code}")
        
        # Prüfen, ob es ein gültiges Bild ist
        try:
            # Versuche die Bilddaten zu verifizieren, indem wir sie mit Pillow öffnen
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(response.content))
            img.verify()  # Verifiziere, dass es ein gültiges Bild ist
            logger.info(f"Gültiges Bild vom Typ {img.format} geladen, Größe: {img.size}")
            img.close()
            
            # Bildaten als Bytes zurückgeben
            return response.content
        except Exception as img_err:
            logger.error(f"Ungültiges Bildformat: {str(img_err)}")
            # Falls das Bild ungültig ist, verwenden wir den ersten Plan aus der Liste
            # Dies ist eine Fallback-Strategie
            logger.info("Verwende Standard-Plan als Fallback")
            if hasattr(auth_client, "available_plans") and len(auth_client.available_plans) > 0:
                default_plan = auth_client.available_plans[0]
                default_url = default_plan.get('url', '')
                if default_url and default_url != plan_url:
                    logger.info(f"Versuche Standard-Plan stattdessen: {default_url}")
                    # Rekursiver Aufruf mit der Standard-URL
                    return await get_specific_plan_image(auth_client, default_url)
            # Wenn auch das nicht funktioniert, ein Platzhalter-Bild verwenden
            raise Exception("Konnte kein gültiges Bild laden")
    except Exception as e:
        logger.error(f"Fehler beim Laden des Plans über URL: {str(e)}")
        raise

async def get_timetable(dsb_client) -> Optional[bytes]:
    """
    Lädt den aktuellen Stundenplan von DSBmobile herunter.
    
    Args:
        dsb_client: Das PyDSB-Objekt
        
    Returns:
        Die Bilddaten des Stundenplans als Base64-String oder None, wenn kein Plan gefunden wurde
    """
    try:
        # Abruf der Pläne in einem ThreadPool, da pydsb nicht nativ asynchron ist
        loop = asyncio.get_event_loop()
        plans = await loop.run_in_executor(None, dsb_client.get_plans)
        
        if not plans:
            logger.warning("Keine Pläne gefunden")
            return None
        
        # Suche nach Stundenplan-Einträgen mit 'MTA' im Titel
        timetable_entries = []
        for plan in plans:
            # Pläne können verschiedene Formate haben
            plan_title = ""
            plan_url = ""
            
            if isinstance(plan, dict):
                if 'url' in plan:
                    plan_url = plan['url']
                if 'title' in plan:
                    plan_title = plan['title']
            elif hasattr(plan, 'url'):
                plan_url = plan.url
                if hasattr(plan, 'title'):
                    plan_title = plan.title
            
            # Nur Einträge mit 'MTA' im Titel hinzufügen
            if plan_url and ('MTA' in plan_title or not plan_title):  # Falls kein Titel vorhanden ist, nehmen wir auch den Plan
                logger.info(f"Gefundener Plan: {plan_title}")
                timetable_entries.append({"url": plan_url, "title": plan_title})
                
        if not timetable_entries:
            # Versuche es mit den Neuigkeiten, falls es keine Pläne gibt
            news = await loop.run_in_executor(None, dsb_client.get_news)
            logger.info(f"Anzahl gefundener Neuigkeiten: {len(news)}")
            
            for item in news:
                item_title = ""
                item_url = ""
                
                if isinstance(item, dict):
                    if 'url' in item:
                        item_url = item['url']
                    if 'title' in item:
                        item_title = item['title']
                elif hasattr(item, 'url'):
                    item_url = item.url
                    if hasattr(item, 'title'):
                        item_title = item.title
                
                # Nur Einträge mit 'MTA' im Titel für Stundenplan hinzufügen
                if item_url and 'MTA' in item_title:
                    logger.info(f"Gefundene Neuigkeit mit MTA: {item_title}")
                    timetable_entries.append({"url": item_url, "title": item_title})
        
        if not timetable_entries:
            logger.warning("Keine Stundenplan-URLs mit MTA im Titel gefunden")
            return None
            
        # Alle gefundenen Pläne loggen
        logger.info(f"Gefundene Timetable-Einträge: {len(timetable_entries)}")
        for idx, entry in enumerate(timetable_entries):
            title = entry.get('title', 'Kein Titel')
            logger.info(f"Plan {idx+1}: {title}")
        
        # Alle gefundenen Pläne auf dem dsb_client Objekt speichern, damit sie später abgerufen werden können
        dsb_client.available_plans = timetable_entries
        
        # Neuesten Stundenplan verwenden
        latest_timetable = timetable_entries[0]
        plan_url = latest_timetable.get('url', '')
        plan_title = latest_timetable.get('title', 'Kein Titel')
        
        logger.info(f"Verwende Stundenplan: {plan_title}")
        
        if not plan_url:
            logger.warning("Keine URL im Stundenplan-Eintrag gefunden")
            return None
            
        # Download des Bildes durchführen
        async with httpx.AsyncClient() as client:
            response = await client.get(plan_url)
            if response.status_code != 200:
                logger.error(f"Fehler beim Herunterladen des Stundenplans: HTTP {response.status_code}")
                return None
                
            image_data = response.content
            logger.info(f"Stundenplan erfolgreich heruntergeladen: {len(image_data)} Bytes")
            
            # Umwandlung in Base64 für einfache Speicherung und Übertragung
            base64_data = base64.b64encode(image_data)
            return base64_data
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Stundenplans: {str(e)}")
        return None
