'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface FollowUpCounts {
  overdue: number
  at_risk: number
  stale: number
  no_response: number
  completed: number
}

interface TaskItem {
  id: number
  title: string
  assigned_to_name: string | null
  days_overdue?: number
  days_left?: number
  days_since_update?: number
  priority: string
  category: string
  due_date: string
}

interface FollowUpSummary {
  overdue: TaskItem[]
  at_risk: TaskItem[]
  stale: TaskItem[]
  no_response: TaskItem[]
  faculty_followup: Record<string, string[]>
  summary_counts: FollowUpCounts
  narrative: string
  generated_at: string
}

interface HistoryEntry {
  id: number
  overdue_count: number
  at_risk_count: number
  stale_count: number
  no_response_count: number
  narrative: string
  created_at: string
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: 'text-red-600 bg-red-50 border-red-200',
  high:     'text-orange-600 bg-orange-50 border-orange-200',
  medium:   'text-yellow-600 bg-yellow-50 border-yellow-200',
  low:      'text-green-600 bg-green-50 border-green-200',
}

function CountCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={`rounded-lg border p-4 ${color}`}>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-sm font-medium mt-1">{label}</div>
    </div>
  )
}

function TaskRow({ task, badge }: { task: TaskItem; badge: string }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded border bg-white hover:shadow-sm transition">
      <span className={`mt-0.5 shrink-0 text-xs font-semibold px-2 py-0.5 rounded border ${PRIORITY_COLORS[task.priority] ?? 'bg-gray-50 border-gray-200 text-gray-600'}`}>
        {task.priority}
      </span>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-900 truncate">{task.title}</p>
        <p className="text-xs text-gray-500 mt-0.5">
          {task.assigned_to_name ?? 'Unassigned'} &middot; {badge}
        </p>
      </div>
      <span className="text-xs text-gray-400 shrink-0">
        {task.category}
      </span>
    </div>
  )
}

export default function FollowUpPage() {
  const [atRiskDays, setAtRiskDays] = useState(3)
  const [staleDays, setStaleDays] = useState(5)
  const [messageDraft, setMessageDraft] = useState<Record<string, string>>({})
  const [activeTab, setActiveTab] = useState<'summary' | 'history'>('summary')

  const { data: summary, isLoading, refetch } = useQuery<FollowUpSummary>({
    queryKey: ['followup-summary', atRiskDays, staleDays],
    queryFn: () =>
      api.get(`/followup/summary?at_risk_days=${atRiskDays}&stale_days=${staleDays}&save=true`)
         .then(r => r.data),
    staleTime: 2 * 60 * 1000,
  })

  const { data: history } = useQuery<HistoryEntry[]>({
    queryKey: ['followup-history'],
    queryFn: () => api.get('/followup/history?limit=10').then(r => r.data),
    staleTime: 60_000,
  })

  const draftMutation = useMutation({
    mutationFn: (body: { assignee_name: string; task_titles: string[]; urgency: string }) =>
      api.post('/followup/message', body).then(r => r.data),
    onSuccess: (data, vars) =>
      setMessageDraft(prev => ({ ...prev, [vars.assignee_name]: data.message })),
  })

  const counts = summary?.summary_counts ?? { overdue: 0, at_risk: 0, stale: 0, no_response: 0, completed: 0 }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Follow-Up Centre</h1>
          {summary && (
            <p className="text-sm text-gray-500 mt-0.5">Generated at {summary.generated_at}</p>
          )}
        </div>
        <div className="flex gap-2 flex-wrap">
          <label className="flex items-center gap-1 text-sm text-gray-600">
            At-risk ≤
            <input
              type="number" min={1} max={14} value={atRiskDays}
              onChange={e => setAtRiskDays(Number(e.target.value))}
              className="w-12 border rounded px-1 py-0.5 text-sm"
            /> days
          </label>
          <label className="flex items-center gap-1 text-sm text-gray-600">
            Stale ≥
            <input
              type="number" min={1} max={30} value={staleDays}
              onChange={e => setStaleDays(Number(e.target.value))}
              className="w-12 border rounded px-1 py-0.5 text-sm"
            /> days
          </label>
          <button
            onClick={() => refetch()}
            className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Tab nav */}
      <div className="flex gap-4 border-b">
        {(['summary', 'history'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2 text-sm font-medium capitalize border-b-2 transition ${
              activeTab === tab
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'summary' ? 'Current Summary' : 'History'}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-48 text-gray-400">
          Analysing tasks...
        </div>
      )}

      {activeTab === 'summary' && summary && (
        <>
          {/* Count cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <CountCard label="Overdue" value={counts.overdue} color="text-red-600 bg-red-50 border-red-200 border" />
            <CountCard label="At Risk" value={counts.at_risk} color="text-orange-600 bg-orange-50 border-orange-200 border" />
            <CountCard label="Stale" value={counts.stale} color="text-yellow-600 bg-yellow-50 border-yellow-200 border" />
            <CountCard label="No Response" value={counts.no_response} color="text-gray-600 bg-gray-50 border-gray-200 border" />
          </div>

          {/* AI Narrative */}
          {summary.narrative && (
            <div className="bg-white border rounded-lg p-5">
              <h2 className="font-semibold text-gray-900 mb-3">AI Narrative Summary</h2>
              <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">
                {summary.narrative}
              </pre>
            </div>
          )}

          {/* Task buckets */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Overdue */}
            {summary.overdue.length > 0 && (
              <div className="bg-white border border-red-200 rounded-lg p-4">
                <h3 className="font-semibold text-red-700 mb-3">
                  Overdue ({summary.overdue.length})
                </h3>
                <div className="space-y-2">
                  {summary.overdue.map(t => (
                    <TaskRow key={t.id} task={t}
                      badge={`${t.days_overdue ?? 0}d overdue`} />
                  ))}
                </div>
              </div>
            )}

            {/* At Risk */}
            {summary.at_risk.length > 0 && (
              <div className="bg-white border border-orange-200 rounded-lg p-4">
                <h3 className="font-semibold text-orange-700 mb-3">
                  At Risk ({summary.at_risk.length})
                </h3>
                <div className="space-y-2">
                  {summary.at_risk.map(t => (
                    <TaskRow key={t.id} task={t}
                      badge={`${t.days_left ?? 0}d left`} />
                  ))}
                </div>
              </div>
            )}

            {/* Stale */}
            {summary.stale.length > 0 && (
              <div className="bg-white border border-yellow-200 rounded-lg p-4">
                <h3 className="font-semibold text-yellow-700 mb-3">
                  Stale ({summary.stale.length})
                </h3>
                <div className="space-y-2">
                  {summary.stale.map(t => (
                    <TaskRow key={t.id} task={t}
                      badge={`No update for ${t.days_since_update ?? 0}d`} />
                  ))}
                </div>
              </div>
            )}

            {/* No Response */}
            {summary.no_response.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-700 mb-3">
                  No Response ({summary.no_response.length})
                </h3>
                <div className="space-y-2">
                  {summary.no_response.map(t => (
                    <TaskRow key={t.id} task={t} badge="Pending, 0% progress" />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Faculty Follow-Up */}
          {Object.keys(summary.faculty_followup).length > 0 && (
            <div className="bg-white border rounded-lg p-5">
              <h2 className="font-semibold text-gray-900 mb-4">Faculty Requiring Follow-Up</h2>
              <div className="space-y-4">
                {Object.entries(summary.faculty_followup).map(([faculty, tasks]) => (
                  <div key={faculty} className="border rounded p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-medium text-gray-900">{faculty}</p>
                        <ul className="mt-1 space-y-0.5 text-sm text-gray-600">
                          {tasks.map((t, i) => <li key={i} className="truncate">• {t}</li>)}
                        </ul>
                      </div>
                      <div className="flex flex-col gap-2 shrink-0">
                        <button
                          onClick={() =>
                            draftMutation.mutate({
                              assignee_name: faculty,
                              task_titles: tasks,
                              urgency: 'high',
                            })
                          }
                          className="px-3 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700"
                          disabled={draftMutation.isPending}
                        >
                          Draft Message
                        </button>
                      </div>
                    </div>
                    {messageDraft[faculty] && (
                      <div className="mt-3 p-3 bg-indigo-50 rounded text-sm text-gray-800 whitespace-pre-wrap">
                        {messageDraft[faculty]}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-3">
          {!history?.length && (
            <p className="text-gray-400 text-sm">No history yet. Run a summary first.</p>
          )}
          {history?.map(entry => (
            <div key={entry.id} className="bg-white border rounded-lg p-4">
              <div className="flex flex-wrap gap-3 mb-2">
                <span className="text-xs text-gray-500">
                  {new Date(entry.created_at).toLocaleString()}
                </span>
                <span className="text-xs text-red-600 font-medium">Overdue: {entry.overdue_count}</span>
                <span className="text-xs text-orange-600 font-medium">At Risk: {entry.at_risk_count}</span>
                <span className="text-xs text-yellow-600 font-medium">Stale: {entry.stale_count}</span>
                <span className="text-xs text-gray-600 font-medium">No Response: {entry.no_response_count}</span>
              </div>
              <details>
                <summary className="text-sm text-indigo-600 cursor-pointer">View narrative</summary>
                <pre className="mt-2 text-sm text-gray-700 whitespace-pre-wrap font-sans">
                  {entry.narrative}
                </pre>
              </details>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
