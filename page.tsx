"use client"

import { useState } from "react"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { KpiCards } from "@/components/dashboard/kpi-cards"
import { RiskTable } from "@/components/dashboard/risk-table"
import { ExplainableAI } from "@/components/dashboard/explainable-ai"
import { AnalyticsCharts } from "@/components/dashboard/analytics-charts"
import { CartelGraph } from "@/components/dashboard/cartel-graph"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LayoutDashboard, BarChart3, Network } from "lucide-react"

export default function DashboardPage() {
  const [selectedTenderId, setSelectedTenderId] = useState("TND-99231")

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header onSelectTender={setSelectedTenderId} />

        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-[1400px] mx-auto space-y-6">
            {/* KPI cards always visible */}
            <KpiCards />

            {/* Tabs */}
            <Tabs defaultValue="tenders">
              <TabsList className="mb-2">
                <TabsTrigger value="tenders" className="gap-2">
                  <LayoutDashboard className="w-4 h-4" />
                  Тендеры
                </TabsTrigger>
                <TabsTrigger value="analytics" className="gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Аналитика
                </TabsTrigger>
                <TabsTrigger value="graph" className="gap-2">
                  <Network className="w-4 h-4" />
                  Граф связей
                </TabsTrigger>
              </TabsList>

              {/* Tab 1: Risk table + ExplainableAI */}
              <TabsContent value="tenders">
                <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
                  <div className="xl:col-span-2">
                    <RiskTable onSelectTender={setSelectedTenderId} />
                  </div>
                  <div className="xl:col-span-1">
                    <ExplainableAI tenderId={selectedTenderId} />
                  </div>
                </div>
              </TabsContent>

              {/* Tab 2: Charts */}
              <TabsContent value="analytics">
                <AnalyticsCharts />
              </TabsContent>

              {/* Tab 3: Cartel graph */}
              <TabsContent value="graph">
                <CartelGraph />
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  )
}
