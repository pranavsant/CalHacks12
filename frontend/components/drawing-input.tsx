"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Card } from "@/components/ui/card"
import { Mic, Upload, Loader2, Sparkles } from "lucide-react"

interface DrawingInputProps {
  onSubmit: (prompt: string, audioFile: File | null, useLetta: boolean) => void
  isLoading: boolean
}

export function DrawingInput({ onSubmit, isLoading }: DrawingInputProps) {
  const [prompt, setPrompt] = useState("")
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [useLetta, setUseLetta] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const handleSubmit = () => {
    if (!prompt.trim() && !audioFile) {
      alert("Please enter a prompt or upload/record audio")
      return
    }
    onSubmit(prompt, audioFile, useLetta)
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setAudioFile(file)
      setPrompt("")
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        const audioFile = new File([audioBlob], "recording.webm", { type: "audio/webm" })
        setAudioFile(audioFile)
        setPrompt("")
        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error("[v0] Error starting recording:", error)
      alert("Failed to access microphone")
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  return (
    <Card className="mx-auto max-w-3xl p-6 sm:p-8">
      <div className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="prompt" className="text-base font-medium">
            Describe your image
          </Label>
          <Textarea
            id="prompt"
            placeholder="A serene mountain landscape at sunset..."
            value={prompt}
            onChange={(e) => {
              setPrompt(e.target.value)
              setAudioFile(null)
            }}
            disabled={isLoading || !!audioFile}
            className="min-h-32 resize-none text-base"
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-border" />
          <span className="text-sm text-muted-foreground">or</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Button
            type="button"
            variant="outline"
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isLoading || !!prompt.trim()}
            className="flex-1 bg-transparent"
          >
            <Mic className="mr-2 h-4 w-4" />
            {isRecording ? "Stop Recording" : "Record Audio"}
          </Button>

          <Button
            type="button"
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading || !!prompt.trim()}
            className="flex-1"
          >
            <Upload className="mr-2 h-4 w-4" />
            Upload Audio
          </Button>
          <input ref={fileInputRef} type="file" accept="audio/*" onChange={handleFileUpload} className="hidden" />
        </div>

        {audioFile && (
          <div className="rounded-lg bg-muted p-3">
            <p className="text-sm text-muted-foreground">
              Audio file: <span className="font-medium text-foreground">{audioFile.name}</span>
            </p>
          </div>
        )}

        <div className="flex items-center justify-between rounded-lg border border-border bg-muted/30 p-4">
          <div className="space-y-0.5">
            <Label htmlFor="letta-toggle" className="text-sm font-medium">
              Use Letta Memory
            </Label>
            <p className="text-xs text-muted-foreground">Enable contextual memory for better results</p>
          </div>
          <Switch id="letta-toggle" checked={useLetta} onCheckedChange={setUseLetta} />
        </div>

        <Button
          onClick={handleSubmit}
          disabled={isLoading || (!prompt.trim() && !audioFile)}
          className="w-full text-base font-medium"
          size="lg"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-5 w-5" />
              Generate Drawing
            </>
          )}
        </Button>
      </div>
    </Card>
  )
}
