import { type NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  try {
    const contentType = request.headers.get("content-type")

    let backendResponse: Response

    if (contentType?.includes("multipart/form-data")) {
      // Handle audio file upload - route to /draw/audio endpoint
      const formData = await request.formData()

      // Backend expects field name "audio", not "file"
      // We need to rename the field if it comes as "file"
      const file = formData.get("file") || formData.get("audio")
      const useLetta = formData.get("use_letta")

      const backendFormData = new FormData()
      if (file) {
        backendFormData.append("audio", file)
      }
      if (useLetta) {
        backendFormData.append("use_letta", useLetta.toString())
      }

      backendResponse = await fetch(`${BACKEND_URL}/draw/audio`, {
        method: "POST",
        body: backendFormData,
      })
    } else {
      // Handle JSON text prompt - route to /draw endpoint
      const body = await request.json()
      backendResponse = await fetch(`${BACKEND_URL}/draw`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      })
    }

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text()
      console.error("[v0] Backend error:", errorText)
      return NextResponse.json({ error: "Failed to generate drawing" }, { status: backendResponse.status })
    }

    const data = await backendResponse.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("[v0] API route error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
