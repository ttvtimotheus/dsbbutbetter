'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { RefreshCw, Calendar, Users, Info } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip'
import { Badge } from './ui/badge'

interface PlanSelectorProps {
  availablePlans: { title: string; url: string }[]
  availableClasses: string[]
  onPlanChange: (plan: { title: string; url: string }) => void
  onClassChange: (className: string) => void
  isLoading: boolean
}

export default function PlanSelector({
  availablePlans,
  availableClasses,
  onPlanChange,
  onClassChange,
  isLoading
}: PlanSelectorProps) {
  const [selectedPlanIndex, setSelectedPlanIndex] = useState(0)
  const [selectedClass, setSelectedClass] = useState<string>('')
  
  // Informationen über den aktuell ausgewählten Plan bereitstellen
  const currentPlan = availablePlans[selectedPlanIndex]

  // Initialisiere die Klasse mit 'all' (alle anzeigen) wenn keine ausgewählt ist
  useEffect(() => {
    if (!selectedClass) {
      setSelectedClass('all')
      onClassChange('all')
    }
  }, [selectedClass, onClassChange])
  
  // Debug-Information
  useEffect(() => {
    console.log("Verfügbare Klassen:", availableClasses);
  }, [availableClasses])

  const handlePlanChange = (value: string) => {
    const index = parseInt(value)
    setSelectedPlanIndex(index)
    onPlanChange(availablePlans[index])
  }

  const handleClassChange = (value: string) => {
    setSelectedClass(value)
    onClassChange(value)
  }

  if (availablePlans.length === 0) return null

  return (
    <TooltipProvider>
      <Card className="mb-6">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-center">
            <CardTitle className="text-xl text-primary">Stundenplan-Steuerung</CardTitle>
            {isLoading && <Badge variant="outline" className="flex items-center gap-1"><RefreshCw className="h-3 w-3 animate-spin" /> Wird geladen</Badge>}
          </div>
          <CardDescription>
            Wähle einen Stundenplan und filtere nach Klasse
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-medium">Verfügbare Pläne</h3>
              </div>
              <Select 
                disabled={isLoading || availablePlans.length === 0}
                value={selectedPlanIndex.toString()} 
                onValueChange={handlePlanChange}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Plan auswählen" />
                </SelectTrigger>
                <SelectContent>
                  {availablePlans.map((plan, index) => (
                    <SelectItem key={index} value={index.toString()}>
                      {plan.title || `Plan ${index + 1}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {currentPlan && (
                <div className="text-xs text-muted-foreground">
                  {currentPlan.title && (
                    <p className="truncate">
                      {currentPlan.title}
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-medium">Klasse filtern</h3>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs text-xs">Du kannst nach einer bestimmten Klasse filtern, um nur die relevanten Einträge anzuzeigen.</p>
                  </TooltipContent>
                </Tooltip>
              </div>
              <Select 
                disabled={isLoading} // Entferne die Bedingung, dass availableClasses leer sein könnte
                value={selectedClass} 
                onValueChange={handleClassChange}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Klasse auswählen" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Alle Klassen</SelectItem>
                  {availableClasses.map((className) => (
                    <SelectItem key={className} value={className}>
                      {className}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {selectedClass && selectedClass !== 'all' && (
                <div className="flex items-center">
                  <Badge className="bg-primary/10 text-primary border-primary/20 hover:bg-primary/20">
                    {selectedClass}
                  </Badge>
                  <span className="text-xs text-muted-foreground ml-2">
                    Nur Einträge für diese Klasse werden angezeigt
                  </span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </TooltipProvider>
  )
}
