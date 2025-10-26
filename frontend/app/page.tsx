"use client"

import { useState } from "react"
import { DrawingInput } from "@/components/drawing-input"
import { DrawingResults } from "@/components/drawing-results"
import type { DrawingResponse } from "@/types/drawing"

export default function Home() {
  const [result, setResult] = useState<DrawingResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (prompt: string, audioFile: File | null, useLetta: boolean) => {
    setIsLoading(true)
    setResult(null)
    setError(null)

    try {
      let response: Response

      if (audioFile) {
        // Send audio file as multipart/form-data
        const formData = new FormData()
        formData.append("file", audioFile)
        formData.append("use_letta", useLetta.toString())

        response = await fetch("/api/draw", {
          method: "POST",
          body: formData,
        })
      } else {
        // Send text prompt as JSON
        response = await fetch("/api/draw", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            prompt,
            use_letta: useLetta,
          }),
        })
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.error || `Server error: ${response.status}`
        throw new Error(errorMessage)
      }

      const data = await response.json()

      // Check if backend returned an error in the response
      if (data.error) {
        throw new Error(data.error)
      }

      setResult(data)
    } catch (error) {
      console.error("[v0] Error generating drawing:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to generate drawing. Please try again."
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-12 text-center">
          <h1 className="mb-3 text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            NeuroPlot
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground leading-relaxed">
            Describe an image with text or voice, and watch AI create it using parametric curves
          </p>
        </div>

        <DrawingInput onSubmit={handleSubmit} isLoading={isLoading} />

        {error && (
          <div className="mx-auto mt-8 max-w-3xl rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">
              <strong className="font-semibold">Error:</strong> {error}
            </p>
          </div>
        )}

        {result && <DrawingResults result={result} />}
      </div>
    </main>
  )
}
