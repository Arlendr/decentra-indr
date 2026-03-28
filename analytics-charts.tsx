"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts"

// ─── Static demo data (replace with /api/analytics in production) ────────────

const riskByCategory = [
  { name: "Строительство", high: 12, medium: 8, low: 20 },
  { name: "IT-услуги",     high: 9,  medium: 6, low: 15 },
  { name: "Транспорт",     high: 7,  medium: 11, low: 18 },
  { name: "Медицина",      high: 5,  medium: 9,  low: 22 },
  { name: "Товары",        high: 3,  medium: 7,  low: 30 },
]

const triggerBreakdown = [
  { name: "Совпадение IP",       value: 38, color: "#ef4444" },
  { name: "Копия спецификации",  value: 27, color: "#f97316" },
  { name: "Ценовая аномалия",    value: 22, color: "#eab308" },
  { name: "Без рисков",          value: 13, color: "#22c55e" },
]

const weeklyTrend = [
  { day: "Пн", analyzed: 1820, flagged: 41 },
  { day: "Вт", analyzed: 2100, flagged: 55 },
  { day: "Ср", analyzed: 1950, flagged: 38 },
  { day: "Чт", analyzed: 2340, flagged: 62 },
  { day: "Пт", analyzed: 2780, flagged: 74 },
  { day: "Сб", analyzed: 890,  flagged: 18 },
  { day: "Вс", analyzed: 610,  flagged: 12 },
]

// ─── Custom tooltip ───────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-xs">
      <p className="font-semibold mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color ?? p.fill }}>
          {p.name}: <span className="font-medium">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

// ─── Component ────────────────────────────────────────────────────────────────
export function AnalyticsCharts() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">

      {/* 1. Bar — риски по категориям */}
      <Card className="xl:col-span-2">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold">Распределение рисков по категориям</CardTitle>
          <p className="text-xs text-muted-foreground">За последние 30 дней</p>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={riskByCategory} barGap={4} barCategoryGap="25%">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 11 }}
              />
              <Bar dataKey="high"   name="Высокий"  fill="#ef4444" radius={[4,4,0,0]} />
              <Bar dataKey="medium" name="Средний"  fill="#f97316" radius={[4,4,0,0]} />
              <Bar dataKey="low"    name="Низкий"   fill="#22c55e" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 2. Pie — типы триггеров */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold">Типы триггеров риска</CardTitle>
          <p className="text-xs text-muted-foreground">Доля от всех флагов</p>
        </CardHeader>
        <CardContent className="flex items-center justify-center">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={triggerBreakdown}
                cx="50%"
                cy="45%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={3}
                dataKey="value"
              >
                {triggerBreakdown.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(v: number, name: string) => [`${v}%`, name]}
                contentStyle={{
                  background: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 11 }}
                formatter={(value) => (
                  <span style={{ color: "hsl(var(--muted-foreground))" }}>{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 3. Line — тренд за неделю */}
      <Card className="md:col-span-2 xl:col-span-3">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold">Активность системы за неделю</CardTitle>
          <p className="text-xs text-muted-foreground">Проанализировано тендеров / выявлено флагов</p>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={weeklyTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis
                dataKey="day"
                tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="analyzed"
                name="Проанализировано"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={{ r: 3, fill: "hsl(var(--primary))" }}
                activeDot={{ r: 5 }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="flagged"
                name="С флагами риска"
                stroke="#ef4444"
                strokeWidth={2}
                dot={{ r: 3, fill: "#ef4444" }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

    </div>
  )
}
