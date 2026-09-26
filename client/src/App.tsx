import { useEffect, useMemo, useState } from 'react'
import './App.css'

type PendingProject = {
  id: string
  tenant_name: string
  name: string
  type: string
  status: string
  start_date: string
  end_date: string
  source_document_id: string
}

type MatchAlert = {
  match_id: string
  synergy_score: number
  my_project: { id: string; name: string }
  external_project: { id: string; tenant_name?: string; name: string }
  temporal_overlap_months: number
  status: string
}

const initialProjects: PendingProject[] = [
  {
    id: 'p_8841',
    tenant_name: 'Utility A',
    name: 'Line 24 Rebuild',
    type: 'transmission',
    status: 'pending_validation',
    start_date: '2027-04-01',
    end_date: '2027-11-01',
    source_document_id: 'doc_9912',
  },
  {
    id: 'p_3321',
    tenant_name: 'Utility B',
    name: 'Substation Alpha Expansion',
    type: 'substation',
    status: 'pending_validation',
    start_date: '2027-07-01',
    end_date: '2027-12-15',
    source_document_id: 'doc_2143',
  },
  {
    id: 'p_1125',
    tenant_name: 'Utility A',
    name: 'ROW Clearing South',
    type: 'right_of_way',
    status: 'pending_validation',
    start_date: '2027-08-01',
    end_date: '2027-10-31',
    source_document_id: 'doc_1954',
  },
]

const mapData = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [-75.16, 39.94],
            [-75.12, 39.95],
            [-75.1, 39.9],
            [-75.15, 39.88],
            [-75.16, 39.94],
          ],
        ],
      },
      properties: {
        project_id: 'p_8841',
        name: 'Line 24 Rebuild',
        tenant_name: 'Utility A',
        match_count: 1,
      },
    },
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [-75.14, 39.92],
            [-75.09, 39.93],
            [-75.08, 39.88],
            [-75.12, 39.87],
            [-75.14, 39.92],
          ],
        ],
      },
      properties: {
        project_id: 'p_3321',
        name: 'Substation Alpha Expansion',
        tenant_name: 'Utility B',
        match_count: 1,
      },
    },
  ],
}

function App() {
  const [pendingProjects, setPendingProjects] = useState<PendingProject[]>(initialProjects)
  const [alerts, setAlerts] = useState<MatchAlert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [projectsRes, alertsRes] = await Promise.all([
          fetch('http://localhost:8000/api/v1/projects/pending'),
          fetch('http://localhost:8000/api/v1/matches/alerts'),
        ])

        if (!projectsRes.ok || !alertsRes.ok) {
          throw new Error('API request failed')
        }

        const [projectsData, alertsData] = await Promise.all([
          projectsRes.json(),
          alertsRes.json(),
        ])

        setPendingProjects(projectsData)
        setAlerts(alertsData.data)
      } catch {
        setPendingProjects(initialProjects)
        setAlerts([
          {
            match_id: 'm_102',
            synergy_score: 85,
            my_project: { id: 'p_8841', name: 'Line 24 Rebuild' },
            external_project: {
              id: 'p_3321',
              tenant_name: 'Utility B',
              name: 'Substation Alpha Expansion',
            },
            temporal_overlap_months: 4,
            status: 'identified',
          },
        ])
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const summary = useMemo(
    () => ({
      totalProjects: pendingProjects.length,
      activeAlerts: alerts.filter((alert) => alert.status !== 'resolved').length,
      avgSynergy: alerts.length
        ? Math.round(
            alerts.reduce((sum, alert) => sum + alert.synergy_score, 0) / alerts.length,
          )
        : 0,
    }),
    [pendingProjects, alerts],
  )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand-row">
            <div className="brand-mark">G</div>
            <div>
              <div className="eyebrow">Utility coordination</div>
              <h1>Gridlock</h1>
            </div>
          </div>

          <nav className="nav">
            <button className="nav-item active">Dashboard</button>
            <button className="nav-item">Projects</button>
            <button className="nav-item">Matches</button>
            <button className="nav-item">Reports</button>
          </nav>
        </div>

        <div className="card compact">
          <div className="card-title">NDA status</div>
          <div className="nda-row">
            <span>Utility A / Utility B</span>
            <strong>Verified</strong>
          </div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <div className="eyebrow">Regional planning overview</div>
            <h2>Grid coordination dashboard</h2>
          </div>
          <button className="primary-btn">Generate FERC report</button>
        </header>

        <section className="stats-grid">
          <div className="stat-card accent">
            <span>Total projects</span>
            <strong>{summary.totalProjects}</strong>
          </div>
          <div className="stat-card">
            <span>Active overlaps</span>
            <strong>{summary.activeAlerts}</strong>
          </div>
          <div className="stat-card">
            <span>Avg. synergy</span>
            <strong>{summary.avgSynergy}/100</strong>
          </div>
          <div className="stat-card">
            <span>Capital saved</span>
            <strong>$42.6M</strong>
          </div>
        </section>

        <section className="content-grid">
          <div className="panel map-panel">
            <div className="panel-header">
              <h3>Map view</h3>
              <span>Q3 2027 · bbox: -76.0,39.5,-74.0,40.5</span>
            </div>

            <div className="map-surface">
              <div className="map-grid" />
              {mapData.features.map((feature) => (
                <div
                  key={feature.properties.project_id}
                  className="map-shape"
                  style={{
                    left: `${18 + (feature.geometry.coordinates[0][0][0] + 75.16) * 220}px`,
                    top: `${30 + (40.1 - feature.geometry.coordinates[0][0][1]) * 230}px`,
                    width: '170px',
                    height: '120px',
                    background:
                      feature.properties.tenant_name === 'Utility A' ? '#3b82f6' : '#14b8a6',
                  }}
                >
                  <span>{feature.properties.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel alert-panel">
            <div className="panel-header">
              <h3>Potential overlaps</h3>
              <button className="ghost-btn">View all</button>
            </div>
            <div className="alerts-list">
              {loading ? (
                <div className="empty-state">Loading alerts...</div>
              ) : alerts.length ? (
                alerts.map((alert) => (
                  <article key={alert.match_id} className="alert-item">
                    <div className="alert-row">
                      <span className="tag">{alert.status}</span>
                      <strong>{alert.synergy_score}/100</strong>
                    </div>
                    <h4>{alert.my_project.name}</h4>
                    <p>
                      vs {alert.external_project.name} ·{' '}
                      {alert.external_project.tenant_name ?? 'External Utility'}
                    </p>
                    <small>{alert.temporal_overlap_months} month temporal overlap</small>
                  </article>
                ))
              ) : (
                <div className="empty-state">No overlaps detected.</div>
              )}
            </div>
          </div>
        </section>

        <section className="panel lower-panel">
          <div className="panel-header">
            <h3>Pending project validation</h3>
            <button className="ghost-btn">Upload doc</button>
          </div>

          <div className="project-table">
            <div className="table-head row">
              <span>Project</span>
              <span>Tenant</span>
              <span>Window</span>
              <span>Source</span>
              <span>Status</span>
            </div>
            {pendingProjects.map((project) => (
              <div key={project.id} className="table-row row">
                <span>{project.name}</span>
                <span>{project.tenant_name}</span>
                <span>
                  {project.start_date} → {project.end_date}
                </span>
                <span>{project.source_document_id}</span>
                <span>
                  <button className="approve-btn">Approve</button>
                </span>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
