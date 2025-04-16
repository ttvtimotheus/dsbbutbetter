"use client"

import { TimetableData } from '@/app/page'
import { cn } from '@/lib/utils'
import { Card } from './ui/card'
import { ScrollArea } from './ui/scroll-area'
import { Badge } from './ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip'

interface TimetableViewProps {
  data: TimetableData
  isLoading: boolean
}

export default function TimetableView({ data, isLoading }: TimetableViewProps) {
  // Extrahieren der eindeutigen Wochentage und Zeitslots mit Fallbacks
  const days = data?.days || []
  const periods = data?.periods || []
  const entries = data?.entries || []
  
  // Generieren einer zufälligen Farbe basierend auf dem Fachnamen (konsistent)
  const getSubjectColor = (subject: string) => {
    // Einfache Hash-Funktion, um eine konsistente Farbe für jeden Fachnamen zu erhalten
    const hash = subject.split('').reduce(
      (acc, char) => char.charCodeAt(0) + ((acc << 5) - acc), 0
    );
    
    // Vordefinierte Farbpalette für Unterrichtsfächer (leichter erkennbare Farben)
    const colors = [
      'bg-blue-100 border-blue-300 text-blue-800',      // Blau
      'bg-green-100 border-green-300 text-green-800',    // Grün
      'bg-purple-100 border-purple-300 text-purple-800', // Lila
      'bg-amber-100 border-amber-300 text-amber-800',    // Amber
      'bg-rose-100 border-rose-300 text-rose-800',       // Rose
      'bg-cyan-100 border-cyan-300 text-cyan-800',       // Cyan
      'bg-indigo-100 border-indigo-300 text-indigo-800', // Indigo
      'bg-emerald-100 border-emerald-300 text-emerald-800', // Smaragd
      'bg-fuchsia-100 border-fuchsia-300 text-fuchsia-800', // Fuchsia
      'bg-orange-100 border-orange-300 text-orange-800', // Orange
    ];
    
    return colors[Math.abs(hash) % colors.length];
  }

  // Platziere die Einträge in einer Matrix für die Tabelle
  const timetableMatrix: { [day: string]: { [period: string]: { subject: string; room: string } } } = {}

  // Matrix initialisieren
  days.forEach(day => {
    timetableMatrix[day] = {}
    periods.forEach(period => {
      timetableMatrix[day][period] = { subject: '', room: '' }
    })
  })

  // Matrix mit Einträgen füllen
  entries.forEach(entry => {
    if (timetableMatrix[entry.day] && periods.includes(entry.period)) {
      timetableMatrix[entry.day][entry.period] = {
        subject: entry.subject,
        room: entry.room
      }
    }
  })

  if (isLoading) {
    return (
      <div className="w-full p-4 space-y-4">
        <div className="h-8 w-full bg-muted rounded-md animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          {Array(30)
            .fill(0)
            .map((_, i) => (
              <div key={i} className="h-24 bg-muted rounded-md animate-pulse" />
            ))}
        </div>
      </div>
    )
  }
  
  // Wenn keine Daten vorhanden sind
  if (!days.length || !periods.length) {
    return (
      <div className="w-full p-8 text-center rounded-lg border-2 border-dashed border-muted-foreground/20">
        <h3 className="text-xl font-semibold mb-2">Kein Stundenplan verfügbar</h3>
        <p className="text-muted-foreground">Es wurden keine Stundenplan-Daten gefunden oder der ausgewählte Filter enthält keine Einträge.</p>
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="w-full space-y-4">
        <div className="text-sm text-muted-foreground">
          Zeige {entries.length} Einträge • Farbliche Markierung nach Fach
        </div>
        
        <ScrollArea className="w-full rounded-lg border shadow-sm">
          <div className="p-1">
            <table className="w-full border-collapse min-w-[650px]">
              <thead>
                <tr>
                  <th className="p-3 bg-muted/50 sticky left-0 z-10"></th>
                  {days.map(day => (
                    <th key={day} className="p-3 bg-muted/50 font-semibold text-center border-b">
                      {day}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {periods.map((period, idx) => (
                  <tr key={period} className={idx % 2 === 0 ? 'bg-muted/10' : ''}>
                    <td className="p-3 font-medium text-center whitespace-nowrap sticky left-0 bg-muted/30 z-10 border-r">
                      {period}
                    </td>
                    {days.map(day => {
                      const cell = timetableMatrix[day]?.[period] || { subject: '', room: '' }
                      const hasContent = !!cell.subject
                      
                      // Details für das Tooltip finden
                      const entryDetails = entries.find(e => 
                        e.day === day && e.period === period
                      )
                      
                      return (
                        <td key={`${day}-${period}`} className="p-1 relative min-w-[120px]">
                          {hasContent ? (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Card className={cn(
                                  "h-full min-h-[5rem] p-3 hover:shadow-md transition-shadow",
                                  getSubjectColor(cell.subject),
                                )}>
                                  <div className="flex flex-col h-full justify-between">
                                    <div className="font-medium">{cell.subject}</div>
                                    {cell.room && (
                                      <Badge variant="outline" className="mt-1 self-start">
                                        {cell.room}
                                      </Badge>
                                    )}
                                  </div>
                                </Card>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="max-w-xs">
                                <div className="text-sm">
                                  <div className="font-bold">{cell.subject}</div>
                                  {entryDetails?.text && (
                                    <div className="mt-1 opacity-90">{entryDetails.text}</div>
                                  )}
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          ) : (
                            <div className="h-full min-h-[5rem] rounded-md p-3 bg-muted/20 border border-dashed border-muted-foreground/10">
                            </div>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ScrollArea>
      </div>
    </TooltipProvider>
  )
}
