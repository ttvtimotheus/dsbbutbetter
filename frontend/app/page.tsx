'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import LoginForm from '@/components/login-form'
import TimetableView from '@/components/timetable-view'
import PlanSelector from '@/components/plan-selector'
import { ModeToggle } from '@/components/mode-toggle'
import { useToast } from '@/components/ui/use-toast'
import { RefreshCcw, School, Clock } from 'lucide-react'

export interface TimetableData {
  days: string[];
  periods: string[];
  entries: {
    day: string;
    period: string;
    subject: string;
    room: string;
    text: string;
  }[];
  last_updated?: string;
}

export default function Home() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [originalTimetableData, setOriginalTimetableData] = useState<TimetableData | null>(null) // Originaldaten
  const [timetableData, setTimetableData] = useState<TimetableData | null>(null) // Gefilterte Daten
  const [availablePlans, setAvailablePlans] = useState<{title: string, url: string}[]>([])
  const [availableClasses, setAvailableClasses] = useState<string[]>([])
  const [selectedPlan, setSelectedPlan] = useState<{title: string, url: string} | null>(null)
  const [selectedClass, setSelectedClass] = useState<string>('all')
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const { toast } = useToast()

  // Filtert die Einträge basierend auf der ausgewählten Klasse
  const filterEntriesByClass = (entries: any[], className: string) => {
    if (className === 'all') return entries;
    
    return entries.filter(entry => {
      // Filtere nach Klassenbezeichnung im Text-Feld (Fall-insensitive Suche)
      return entry.text?.toLowerCase().includes(className.toLowerCase());
    });
  };
  
  // Aktualisiere gefilterte Einträge, wenn sich die ausgewählte Klasse ändert
  useEffect(() => {
    if (originalTimetableData && originalTimetableData.entries) {
      console.log(`Filtere nach Klasse: ${selectedClass}`);
      console.log(`Originale Einträge: ${originalTimetableData.entries.length}`);
      
      const filteredEntries = filterEntriesByClass(originalTimetableData.entries, selectedClass);
      console.log(`Gefilterte Einträge: ${filteredEntries.length}`);
      
      const filteredData = {
        ...originalTimetableData,
        entries: filteredEntries
      };
      
      setTimetableData(filteredData);
    }
  }, [selectedClass, originalTimetableData]);

  const handleLogin = async (username: string, password: string) => {
    setIsLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/api/dsb/parse-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Fehler beim Abrufen des Stundenplans')
      }
      
      const data = await response.json()
      console.log('Empfangene Daten vom Backend:', data)
      console.log('Timetable-Struktur:', data.timetable)
      
      // Verfügbare Pläne und Klassen speichern
      setAvailablePlans(data.available_plans || [])
      setAvailableClasses(data.available_classes || [])
      
      // Ersten Plan als Standard auswählen, wenn verfügbar
      if (data.available_plans && data.available_plans.length > 0) {
        setSelectedPlan(data.available_plans[0])
      }
      
      // Sicherstellen, dass die Timetable-Struktur korrekt ist
      if (data.timetable && !data.timetable.entries) {
        console.warn('Keine Einträge in der Timetable gefunden!')
      }
      
      // Original-Daten und gefilterte Daten speichern
      setOriginalTimetableData(data.timetable)
      setTimetableData(data.timetable) // Initial ungefiltert
      setLastUpdated(data.last_updated)
      
      toast({
        title: "Stundenplan geladen",
        description: data.from_cache 
          ? "Stundenplan aus dem Cache geladen" 
          : "Aktueller Stundenplan erfolgreich geladen",
      })
    } catch (error) {
      console.error('Fehler:', error)
      toast({
        title: "Fehler",
        description: error instanceof Error ? error.message : "Fehler beim Laden des Stundenplans",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleReload = () => {
    // Wenn wir bereits einen Stundenplan geladen haben, können wir direkt den neuesten abrufen
    handleLogin(localStorage.getItem('dsb_username') || '', localStorage.getItem('dsb_password') || '')
  }

  return (
    <main className="flex min-h-screen flex-col p-4 md:p-8 lg:p-12 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-3">
          <School className="h-8 w-8 text-primary" />
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">DSB but better</h1>
        </div>
        <ModeToggle />
      </div>
      
      {!timetableData ? (
        <div className="flex flex-col items-center justify-center py-10">
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <School className="h-12 w-12 text-primary mx-auto" />
              <h2 className="mt-6 text-3xl font-extrabold">Willkommen</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Melde dich mit deinen DSBmobile-Zugangsdaten an, um deinen Stundenplan zu sehen
              </p>
            </div>
            
            <Card className="w-full border shadow-lg">
              <CardHeader>
                <CardTitle>Stundenplan laden</CardTitle>
                <CardDescription>
                  Bitte gib deine DSBmobile Zugangsdaten ein
                </CardDescription>
              </CardHeader>
              <CardContent>
                <LoginForm onLogin={handleLogin} isLoading={isLoading} />
              </CardContent>
            </Card>
            
            <div className="text-center text-xs text-muted-foreground mt-4">
              <p>Diese Anwendung speichert deine DSBmobile-Zugangsdaten nur für die aktuelle Sitzung</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="w-full">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
            <div>
              <h2 className="text-2xl font-semibold flex items-center gap-2">
                <School className="h-5 w-5 text-primary" /> 
                Dein Stundenplan
              </h2>
              {lastUpdated && (
                <div className="flex items-center gap-1 mt-1">
                  <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Zuletzt aktualisiert: {lastUpdated}
                  </p>
                </div>
              )}
            </div>
            <Button onClick={handleReload} disabled={isLoading} className="min-w-32 transition-all" variant="outline">
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <RefreshCcw className="h-4 w-4 animate-spin" /> Lädt...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <RefreshCcw className="h-4 w-4" /> Neu laden
                </span>
              )}
            </Button>
          </div>
          
          {/* Plan- und Klassenauswahl */}
          <PlanSelector 
            availablePlans={availablePlans}
            availableClasses={availableClasses}
            onPlanChange={(plan) => {
              setSelectedPlan(plan);
              console.log('Plan geändert:', plan);
              
              // API-Call, um den spezifischen Plan zu laden
              if (plan.url) {
                setIsLoading(true);
                
                // Anfrage, um den spezifischen Plan zu laden
                fetch('http://localhost:8000/api/dsb/get-specific-plan', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    username: localStorage.getItem('dsb_username') || '',
                    password: localStorage.getItem('dsb_password') || '',
                    plan_url: plan.url
                  }),
                })
                .then(response => {
                  if (!response.ok) {
                    throw new Error('Fehler beim Laden des Plans');
                  }
                  return response.json();
                })
                .then(data => {
                  console.log('Plan erfolgreich geladen:', data);
                  setOriginalTimetableData(data.timetable);
                  setTimetableData(data.timetable);
                  setLastUpdated(data.last_updated);
                  
                  toast({
                    title: "Plan gewechselt",
                    description: `${plan.title} wurde erfolgreich geladen`,
                  });
                })
                .catch(error => {
                  console.error('Fehler beim Laden des Plans:', error);
                  toast({
                    title: "Fehler",
                    description: error.message,
                    variant: "destructive",
                  });
                })
                .finally(() => {
                  setIsLoading(false);
                });
              }
            }}
            onClassChange={(className) => {
              setSelectedClass(className);
              console.log('Klasse geändert:', className);
            }}
            isLoading={isLoading}
          />
          
          <TimetableView data={timetableData} isLoading={isLoading} />
        </div>
      )}
    </main>
  )
}
