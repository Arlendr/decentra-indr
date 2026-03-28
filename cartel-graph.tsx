"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Network, AlertTriangle, Info } from "lucide-react"
import { cn } from "@/lib/utils"

// ─── Graph data (static demo — replace with /api/graph in production) ─────────

interface GraphNode {
  id: string
  label: string
  bin: string
  type: "cartel" | "legit" | "hub"
  x: number
  y: number
}

interface GraphEdge {
  from: string
  to: string
  type: "ip_match" | "phone_match" | "co_bid" | "clean"
  weight: number
  label: string
}

const NODES: GraphNode[] = [
  // Картельный кластер
  { id: "c1", label: "ТОО АлфаГрупп",  bin: "999000000001", type: "hub",    x: 300, y: 180 },
  { id: "c2", label: "ТОО БетаСнаб",   bin: "999000000002", type: "cartel", x: 160, y: 300 },
  { id: "c3", label: "ТОО ГаммаТрейд", bin: "999000000003", type: "cartel", x: 440, y: 300 },
  // Легитимные участники
  { id: "l1", label: "ТОО СтройСервис",  bin: "100000000001", type: "legit", x: 90,  y: 130 },
  { id: "l2", label: "ТОО АлматыСнаб",   bin: "100000000002", type: "legit", x: 510, y: 130 },
  { id: "l3", label: "ТОО НурСтрой",     bin: "100000000003", type: "legit", x: 90,  y: 420 },
  { id: "l4", label: "ТОО АстанаТрейд",  bin: "100000000004", type: "legit", x: 510, y: 420 },
]

const EDGES: GraphEdge[] = [
  { from: "c1", to: "c2", type: "ip_match",    weight: 3, label: "IP: 10.0.0.99" },
  { from: "c1", to: "c3", type: "phone_match", weight: 2, label: "Тел. совпадение" },
  { from: "c2", to: "c3", type: "ip_match",    weight: 4, label: "Ротация (8 тенд.)" },
  { from: "c1", to: "l1", type: "co_bid",      weight: 1, label: "Совм. участие" },
  { from: "c1", to: "l2", type: "co_bid",      weight: 1, label: "Совм. участие" },
  { from: "c2", to: "l3", type: "co_bid",      weight: 1, label: "Совм. участие" },
  { from: "c3", to: "l4", type: "co_bid",      weight: 1, label: "Совм. участие" },
]

const EDGE_COLORS: Record<GraphEdge["type"], string> = {
  ip_match:    "#ef4444",
  phone_match: "#f97316",
  co_bid:      "#94a3b8",
  clean:       "#22c55e",
}

const NODE_COLORS: Record<GraphNode["type"], { fill: string; stroke: string; text: string }> = {
  hub:    { fill: "#fef2f2", stroke: "#ef4444", text: "#991b1b" },
  cartel: { fill: "#fff7ed", stroke: "#f97316", text: "#9a3412" },
  legit:  { fill: "#f0fdf4", stroke: "#22c55e", text: "#166534" },
}

// ─── Component ─────────────────────────────────────────────────────────────────
export function CartelGraph() {
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [hoveredEdge, setHoveredEdge] = useState<GraphEdge | null>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  const W = 600
  const H = 520

  function getNode(id: string) {
    return NODES.find((n) => n.id === id)!
  }

  return (
    <Card className="border-red-500/20">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-red-500/10 shrink-0">
              <Network className="w-5 h-5 text-red-500" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold leading-tight">Граф связей поставщиков</CardTitle>
              <p className="text-xs text-muted-foreground">Обнаружен 1 картельный кластер</p>
            </div>
          </div>
          <Badge className="bg-red-500/10 text-red-600 border-red-500/30 border gap-1">
            <AlertTriangle className="w-3 h-3" />
            Картель выявлен
          </Badge>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-3 pt-1">
          {[
            { color: "#ef4444", label: "Совпадение IP" },
            { color: "#f97316", label: "Совпадение телефона" },
            { color: "#94a3b8", label: "Совместное участие" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1.5">
              <div className="w-5 h-0.5 rounded-full" style={{ background: item.color }} />
              <span className="text-xs text-muted-foreground">{item.label}</span>
            </div>
          ))}
          {[
            { fill: "#fef2f2", stroke: "#ef4444", label: "Центр кластера" },
            { fill: "#fff7ed", stroke: "#f97316", label: "Картельная компания" },
            { fill: "#f0fdf4", stroke: "#22c55e", label: "Чистая компания" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded-full border"
                style={{ background: item.fill, borderColor: item.stroke }}
              />
              <span className="text-xs text-muted-foreground">{item.label}</span>
            </div>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        <div className="relative overflow-hidden rounded-xl border border-border bg-secondary/20">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${W} ${H}`}
            className="w-full"
            style={{ maxHeight: 420 }}
          >
            <defs>
              {/* Арrowhead маркеры */}
              {Object.entries(EDGE_COLORS).map(([type, color]) => (
                <marker
                  key={type}
                  id={`arrow-${type}`}
                  markerWidth="8"
                  markerHeight="8"
                  refX="6"
                  refY="3"
                  orient="auto"
                >
                  <path d="M0,0 L0,6 L8,3 z" fill={color} opacity="0.7" />
                </marker>
              ))}

              {/* Glow filter для картельных нод */}
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>

              {/* Pulse animation для hub */}
              <filter id="pulse">
                <feGaussianBlur stdDeviation="5" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Background grid */}
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="hsl(var(--border))" strokeWidth="0.5" />
            </pattern>
            <rect width={W} height={H} fill="url(#grid)" opacity="0.4" />

            {/* Edges */}
            {EDGES.map((edge, i) => {
              const from = getNode(edge.from)
              const to   = getNode(edge.to)
              const isHovered = hoveredEdge === edge || hoveredNode?.id === edge.from || hoveredNode?.id === edge.to
              const color = EDGE_COLORS[edge.type]

              // Midpoint for label
              const mx = (from.x + to.x) / 2
              const my = (from.y + to.y) / 2

              return (
                <g key={i}>
                  <line
                    x1={from.x} y1={from.y}
                    x2={to.x}   y2={to.y}
                    stroke={color}
                    strokeWidth={isHovered ? edge.weight * 2 + 1 : edge.weight * 1.5}
                    strokeOpacity={isHovered ? 1 : 0.55}
                    strokeDasharray={edge.type === "co_bid" ? "6,4" : undefined}
                    markerEnd={`url(#arrow-${edge.type})`}
                    className="transition-all duration-200 cursor-pointer"
                    onMouseEnter={() => setHoveredEdge(edge)}
                    onMouseLeave={() => setHoveredEdge(null)}
                  />
                  {isHovered && (
                    <g>
                      <rect
                        x={mx - 56} y={my - 12}
                        width={112} height={22}
                        rx={6} fill="hsl(var(--card))"
                        stroke={color} strokeWidth={1}
                        filter="url(#glow)"
                      />
                      <text
                        x={mx} y={my + 3}
                        textAnchor="middle"
                        fontSize={10}
                        fill={color}
                        fontWeight="600"
                      >
                        {edge.label}
                      </text>
                    </g>
                  )}
                </g>
              )
            })}

            {/* Nodes */}
            {NODES.map((node) => {
              const colors = NODE_COLORS[node.type]
              const isHovered = hoveredNode?.id === node.id
              const isCartelRelated = ["c1","c2","c3"].includes(node.id)
              const r = node.type === "hub" ? 36 : 28

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  className="cursor-pointer"
                  onMouseEnter={() => setHoveredNode(node)}
                  onMouseLeave={() => setHoveredNode(null)}
                >
                  {/* Pulsing ring for cartel nodes */}
                  {isCartelRelated && (
                    <circle
                      r={r + 8}
                      fill="none"
                      stroke={colors.stroke}
                      strokeWidth={1}
                      opacity="0.3"
                      className="animate-ping"
                      style={{ animationDuration: "2.5s" }}
                    />
                  )}

                  {/* Shadow */}
                  <circle
                    r={r + 2}
                    fill={colors.stroke}
                    opacity={isHovered ? 0.25 : 0.12}
                    className="transition-all duration-200"
                  />

                  {/* Main circle */}
                  <circle
                    r={r}
                    fill={colors.fill}
                    stroke={colors.stroke}
                    strokeWidth={isHovered ? 3 : 2}
                    filter={isCartelRelated ? "url(#glow)" : undefined}
                    className="transition-all duration-200"
                  />

                  {/* Label inside */}
                  <text
                    textAnchor="middle"
                    y={-6}
                    fontSize={node.type === "hub" ? 9 : 8}
                    fill={colors.text}
                    fontWeight="700"
                  >
                    {node.label.split(" ")[1]?.slice(0, 8) ?? node.label.slice(0, 8)}
                  </text>
                  <text
                    textAnchor="middle"
                    y={6}
                    fontSize={7}
                    fill={colors.text}
                    opacity={0.7}
                  >
                    {node.label.split(" ")[2]?.slice(0, 8) ?? ""}
                  </text>

                  {/* Risk icon for cartel */}
                  {node.type === "hub" && (
                    <text textAnchor="middle" y={18} fontSize={12}>⚠️</text>
                  )}

                  {/* Hover tooltip */}
                  {isHovered && (
                    <g transform={`translate(${node.x < 300 ? 40 : -160}, -50)`}>
                      <rect
                        width={155} height={54}
                        rx={8} fill="hsl(var(--card))"
                        stroke={colors.stroke} strokeWidth={1.5}
                      />
                      <text x={10} y={18} fontSize={11} fill="hsl(var(--foreground))" fontWeight="600">
                        {node.label}
                      </text>
                      <text x={10} y={33} fontSize={9} fill="hsl(var(--muted-foreground))">
                        БИН: {node.bin}
                      </text>
                      <text x={10} y={46} fontSize={9} fill={colors.stroke} fontWeight="600">
                        {node.type === "hub" ? "⚠️ Центр картеля" :
                         node.type === "cartel" ? "🔴 Подозреваемый" : "✅ Чистая компания"}
                      </text>
                    </g>
                  )}
                </g>
              )
            })}
          </svg>

          {/* Info banner at bottom */}
          <div className="absolute bottom-0 left-0 right-0 bg-red-500/8 border-t border-red-500/20 px-4 py-2.5 flex items-center gap-2">
            <Info className="w-3.5 h-3.5 text-red-500 shrink-0" />
            <p className="text-xs text-red-600">
              <strong>ТОО АлфаГрупп, БетаСнаб, ГаммаТрейд</strong> — подали заявки с одного IP-адреса (10.0.0.99).
              Компании ротировали победы в 8 совместных тендерах.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
