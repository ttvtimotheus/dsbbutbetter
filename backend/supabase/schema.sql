-- Erstellen der Tabelle für Stundenpläne
CREATE TABLE IF NOT EXISTS timetables (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    data TEXT NOT NULL, -- JSON-Daten als Text gespeichert
    image TEXT NOT NULL, -- Base64-kodiertes Bild
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Index für schnelle Abfragen nach Benutzernamen
    CONSTRAINT idx_timetables_username UNIQUE (username, timestamp)
);

-- RLS (Row Level Security) für die Tabelle aktivieren
ALTER TABLE timetables ENABLE ROW LEVEL SECURITY;

-- Policy für authentifizierte Benutzer (optional, wenn Sie Auth verwenden)
CREATE POLICY "Benutzer können nur ihre eigenen Daten sehen" ON timetables
    FOR SELECT USING (auth.uid()::text = username);

CREATE POLICY "Benutzer können nur ihre eigenen Daten einfügen" ON timetables
    FOR INSERT WITH CHECK (auth.uid()::text = username);

-- Erstellen einer Funktion zum Löschen alter Einträge (optional)
CREATE OR REPLACE FUNCTION delete_old_timetables()
RETURNS TRIGGER AS $$
BEGIN
    -- Lösche Einträge, die älter als 30 Tage sind
    DELETE FROM timetables
    WHERE timestamp < NOW() - INTERVAL '30 days';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Erstellen eines Triggers, der die Funktion ausführt
CREATE TRIGGER trigger_delete_old_timetables
AFTER INSERT ON timetables
EXECUTE FUNCTION delete_old_timetables();
