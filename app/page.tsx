"use client"

import { useState, useRef } from "react"
import { ref, uploadBytes, getDownloadURL } from "firebase/storage"
import { storage } from "@/lib/firebase"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Activity, Heart, Thermometer, User, Calendar, Phone, Mail, Mic, MicOff, Save, Edit3 } from "lucide-react"

export default function PatientDashboard() {
  const [isRecording, setIsRecording] = useState(false)
  const [notes, setNotes] = useState(`Patient shows improvement in mobility since last visit. 
Vital signs are stable and within normal range. 
Continue current medication regimen.
Follow-up appointment scheduled for next week.`) //placeholder..will remove later
  const [isEditingNotes, setIsEditingNotes] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  // Mock patient data
  const patientData = {
    name: "Sarah Johnson",
    age: 45,
    id: "PT-2024-001",
    phone: "(555) 123-4567",
    email: "sarah.johnson@email.com",
    lastVisit: "2024-01-10",
    nextAppointment: "2024-01-17",
    vitals: {
      heartRate: 72,
      bloodPressure: "120/80",
      temperature: 98.6,
      oxygenSat: 98,
    },
    conditions: ["Hypertension", "Type 2 Diabetes"],
    medications: ["Metformin 500mg", "Lisinopril 10mg", "Aspirin 81mg"],
  }

  const handleRecord = async () => {
   if (!isRecording) {
      // Start recording
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        const patientId = "P001" // example; replace with dynamic patient ID
        const storageRef = ref(storage, `patients/${patientId}/recordings/${Date.now()}.webm`)

        // Upload to Firebase Storage
        await uploadBytes(storageRef, audioBlob)
        const audioUrl = await getDownloadURL(storageRef)

        // Send to backend for transcription
        const res = await fetch("/api/transcribe", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ audioUrl, patientId }),
        })

        const data = await res.json()
        setNotes(data.transcript) // pre-fill notes for doctor
      }

      mediaRecorder.start()
      setIsRecording(true)
    } else {
      // Stop recording
      mediaRecorderRef.current?.stop()
      setIsRecording(false)
    } 
    
    // setIsRecording(!isRecording)
    // // In a real app, this would start/stop audio recording
    // console.log(isRecording ? "Stopping recording..." : "Starting recording...")
  }

  const handleSaveNotes = () => {
    setIsEditingNotes(false)
    // In a real app, this would save to database
    console.log("Notes saved:", notes)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground font-[family-name:var(--font-space-grotesk)]">
                Patient Data Management
              </h1>
              <p className="text-muted-foreground">Professional healthcare dashboard</p>
            </div>
            <Button
              onClick={handleRecord}
              variant={isRecording ? "destructive" : "default"}
              size="lg"
              className="flex items-center gap-2"
            >
              {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
              {isRecording ? "Stop Recording" : "Record Data"}
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="dashboard">Patient Dashboard</TabsTrigger>
            <TabsTrigger value="record">Record Data</TabsTrigger>
            <TabsTrigger value="summary">Summary & Notes</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Patient Info Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Patient Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold">{patientData.name}</h3>
                    <p className="text-muted-foreground">Age: {patientData.age}</p>
                    <p className="text-muted-foreground">ID: {patientData.id}</p>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4" />
                      <span>{patientData.phone}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      <span>{patientData.email}</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      <span>Last Visit: {patientData.lastVisit}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      <span>Next: {patientData.nextAppointment}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Vital Signs */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Heart Rate</p>
                      <p className="text-2xl font-bold">{patientData.vitals.heartRate}</p>
                      <p className="text-xs text-muted-foreground">bpm</p>
                    </div>
                    <Heart className="h-8 w-8 text-primary" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Blood Pressure</p>
                      <p className="text-2xl font-bold">{patientData.vitals.bloodPressure}</p>
                      <p className="text-xs text-muted-foreground">mmHg</p>
                    </div>
                    <Activity className="h-8 w-8 text-primary" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Temperature</p>
                      <p className="text-2xl font-bold">{patientData.vitals.temperature}</p>
                      <p className="text-xs text-muted-foreground">°F</p>
                    </div>
                    <Thermometer className="h-8 w-8 text-primary" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Oxygen Sat</p>
                      <p className="text-2xl font-bold">{patientData.vitals.oxygenSat}</p>
                      <p className="text-xs text-muted-foreground">%</p>
                    </div>
                    <Activity className="h-8 w-8 text-primary" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Conditions and Medications */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Current Conditions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {patientData.conditions.map((condition, index) => (
                      <Badge key={index} variant="secondary">
                        {condition}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Current Medications</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {patientData.medications.map((medication, index) => (
                      <div key={index} className="p-2 bg-muted rounded-md">
                        {medication}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Record Data Tab */}
          <TabsContent value="record" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Record New Data</CardTitle>
                <CardDescription>Enter new patient data or use voice recording</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="heart-rate">Heart Rate (bpm)</Label>
                    <Input id="heart-rate" type="number" placeholder="72" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="blood-pressure">Blood Pressure</Label>
                    <Input id="blood-pressure" placeholder="120/80" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="temperature">Temperature (°F)</Label>
                    <Input id="temperature" type="number" step="0.1" placeholder="98.6" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="oxygen">Oxygen Saturation (%)</Label>
                    <Input id="oxygen" type="number" placeholder="98" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="observations">Clinical Observations</Label>
                  <Textarea
                    id="observations"
                    placeholder="Enter clinical observations, symptoms, or notes..."
                    className="min-h-[120px]"
                  />
                </div>

                <div className="flex gap-2">
                  <Button className="flex-1">Save Data</Button>
                  <Button
                    variant="outline"
                    onClick={handleRecord}
                    className={isRecording ? "bg-destructive text-destructive-foreground" : ""}
                  >
                    {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Summary & Notes Tab */}
          <TabsContent value="summary" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Patient Summary & Notes</CardTitle>
                    <CardDescription>Real-time editable patient notes and summary</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => setIsEditingNotes(!isEditingNotes)}>
                    <Edit3 className="h-4 w-4 mr-2" />
                    {isEditingNotes ? "View" : "Edit"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {isEditingNotes ? (
                  <div className="space-y-4">
                    <Textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      className="min-h-[300px]"
                      placeholder="Enter patient notes..."
                    />
                    <div className="flex gap-2">
                      <Button onClick={handleSaveNotes}>
                        <Save className="h-4 w-4 mr-2" />
                        Save Notes
                      </Button>
                      <Button variant="outline" onClick={() => setIsEditingNotes(false)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="prose max-w-none">
                    <div className="whitespace-pre-wrap bg-muted p-4 rounded-md">{notes}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
