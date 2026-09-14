import React, { useState, useEffect, useCallback } from 'react'
import type { IncidentSummary } from './types'
import { useIncidents } from './hooks/useIncidents'
import { useAnalytics } from './hooks/useAnalytics'
import { useBuses } from './hooks/useBuses'
import { useScanManager } from './hooks/useScanManager'
import { Sidebar, type NavTab } from './components/Navigation/Sidebar'
import { TopHeader } from './components/Navigation/TopHeader'
import { HomeView } from './components/Views/HomeView'
import { LiveDetectionView } from './components/Views/LiveDetectionView'
import { RoadMapView } from './components/Views/RoadMapView'
import { ReportsView } from './components/Views/ReportsView'
import { BusFleetView } from './components/Views/BusFleetView'
import { AnalyticsView } from './components/Views/AnalyticsView'
import { TransportAuthorityView } from './components/Views/TransportAuthorityView'
import { FieldOpsView } from './components/Views/FieldOpsView'
import { DetailDrawer } from './components/DetailDrawer/DetailDrawer'

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('home')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedIncident, setSelectedIncident] = useState<IncidentSummary | null>(null)
  const [lastSyncTime, setLastSyncTime] = useState<string>('Just now')

  const { incidents, refetch: refetchIncidents } = useIncidents({})
  const { analytics, refetch: refetchAnalytics } = useAnalytics()
  const { buses, refetch: refetchBuses } = useBuses()

  const handleRefreshAll = useCallback(() => {
    refetchIncidents()
    refetchAnalytics()
    refetchBuses()
  }, [refetchIncidents, refetchAnalytics, refetchBuses])

  // Scan state lifted to root level: continues polling & preserving status when changing tabs
  const scanManager = useScanManager({ onScanComplete: handleRefreshAll })

  // Track sync time
  useEffect(() => {
    const now = new Date()
    setLastSyncTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
  }, [incidents, analytics, buses])

  // Keep selectedIncident synchronized with latest polled data
  useEffect(() => {
    if (selectedIncident) {
      const match = incidents.find((i) => i.incident_id === selectedIncident.incident_id)
      if (match) {
        setSelectedIncident(match)
      }
    }
  }, [incidents])

  const activeBusesCount = buses.length || analytics?.active_buses || 24

  return (
    <div className="city-vision-app">
      {/* 1. Left Fixed Navigation Rail (280px) */}
      <Sidebar
        activeTab={currentTab}
        onSelectTab={setCurrentTab}
        activeBusesCount={activeBusesCount}
        isScanProcessing={scanManager.scanStatus.status === 'PROCESSING'}
        scanEventsCount={scanManager.scanStatus.events_dispatched}
      />

      {/* 2. Main Content Area */}
      <div className="app-main-content">
        {/* Fixed Top Header */}
        <TopHeader
          activeBusesCount={activeBusesCount}
          lastUpdated={lastSyncTime}
          onRefreshAll={handleRefreshAll}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          scanManager={scanManager}
          onNavigateTab={setCurrentTab}
        />

        {/* Dynamic Main View */}
        <main className="main-view-container">
          {currentTab === 'home' && (
            <HomeView
              analytics={analytics}
              incidents={incidents}
              buses={buses}
              onNavigateTab={setCurrentTab}
              onSelectIncident={setSelectedIncident}
            />
          )}

          {currentTab === 'live-detection' && (
            <LiveDetectionView
              scanManager={scanManager}
              onSelectIncident={setSelectedIncident}
            />
          )}

          {currentTab === 'road-map' && (
            <RoadMapView
              incidents={incidents}
              buses={buses}
              onSelectIncident={setSelectedIncident}
            />
          )}

          {currentTab === 'transport-authority' && (
            <TransportAuthorityView
              incidents={incidents}
              buses={buses}
              onSelectIncident={setSelectedIncident}
            />
          )}

          {currentTab === 'field-ops' && (
            <FieldOpsView
              incidents={incidents}
              onSelectIncident={setSelectedIncident}
              onRefresh={handleRefreshAll}
            />
          )}

          {currentTab === 'reports' && (
            <ReportsView
              incidents={incidents}
              onSelectIncident={setSelectedIncident}
              onRefresh={handleRefreshAll}
            />
          )}

          {currentTab === 'bus-fleet' && (
            <BusFleetView
              buses={buses}
              onNavigateTab={setCurrentTab}
            />
          )}

          {currentTab === 'analytics' && (
            <AnalyticsView
              analytics={analytics}
              buses={buses}
            />
          )}
        </main>
      </div>

      {/* 3. Global Floating Detail Drawer */}
      <DetailDrawer
        incidentSummary={selectedIncident}
        onClose={() => setSelectedIncident(null)}
        onRefresh={handleRefreshAll}
      />
    </div>
  )
}

export default App
