"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { DrawingResponse } from "@/types/drawing"
import { Star } from "lucide-react"

interface DrawingResultsProps {
  result: DrawingResponse
}

export function DrawingResults({ result }: DrawingResultsProps) {
  return (
    <div className="mx-auto mt-12 max-w-6xl space-y-8">
      <div className="text-center">
        <h2 className="mb-2 text-3xl font-bold text-foreground">Your Generated Drawing</h2>
        <p className="text-muted-foreground">Created using parametric curves</p>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        <Card className="overflow-hidden p-0">
          <div className="bg-muted/30 p-4">
            <h3 className="text-lg font-semibold text-foreground">Generated Image</h3>
            {result.prompt && (
              <p className="mt-2 text-sm italic text-muted-foreground">
                Prompt: &quot;{result.prompt}&quot;
              </p>
            )}
          </div>
          <div className="flex items-center justify-center bg-card p-8">
            <img
              src={result.image_base64}
              alt={`Drawing of ${result.prompt || "generated image"}`}
              className="max-h-96 w-full rounded-lg object-contain"
            />
          </div>
        </Card>

        <div className="space-y-6">
          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-foreground">Evaluation Score</h3>
              <Badge variant="secondary" className="flex items-center gap-1 text-base">
                <Star className="h-4 w-4 fill-primary text-primary" />
                {result.evaluation_score.toFixed(1)} / 10
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Iterations</span>
                <span className="font-medium text-foreground">{result.iterations}</span>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold text-foreground">Parametric Functions</h3>
            <div className="space-y-4">
              {/* Display relative_program segments if available, otherwise fall back to parametric_functions */}
              {result.relative_program?.segments.map((segment, index) => (
                <div key={index} className="space-y-2 rounded-lg bg-muted/50 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">{segment.name}</span>
                    <Badge variant="outline" className="text-xs">
                      t ∈ [{segment.t_min.toFixed(2)}, {segment.t_max.toFixed(2)}]
                    </Badge>
                  </div>
                  <div className="space-y-1 font-mono text-sm">
                    <div className="text-foreground">
                      <span className="text-muted-foreground">x(t) = </span>
                      {segment.x_rel}
                    </div>
                    <div className="text-foreground">
                      <span className="text-muted-foreground">y(t) = </span>
                      {segment.y_rel}
                    </div>
                  </div>
                  {segment.pen.color !== "none" && (
                    <div className="mt-1 flex items-center gap-2">
                      <div
                        className="h-3 w-3 rounded-full border border-gray-300"
                        style={{ backgroundColor: segment.pen.color }}
                      />
                      <span className="text-xs text-muted-foreground">
                        {segment.pen.color === "#000000" ? "Black" : "Blue"}
                      </span>
                    </div>
                  )}
                </div>
              )) || result.parametric_functions?.map((func, index) => (
                <div key={index} className="space-y-2 rounded-lg bg-muted/50 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Segment {index + 1}</span>
                    <Badge variant="outline" className="text-xs">
                      t ∈ [{func.t_start.toFixed(2)}, {func.t_end.toFixed(2)}]
                    </Badge>
                  </div>
                  <div className="space-y-1 font-mono text-sm">
                    <div className="text-foreground">
                      <span className="text-muted-foreground">x(t) = </span>
                      {func.x_t}
                    </div>
                    <div className="text-foreground">
                      <span className="text-muted-foreground">y(t) = </span>
                      {func.y_t}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
