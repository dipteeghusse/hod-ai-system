'use client'

import AppShell from '@/components/Shared/AppShell'
import { agentApi } from '@/lib/api'
import { useConfig } from '@/lib/useConfig'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Shield, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'

// Default status for each criterion — in a real system this comes from DB
const DEFAULT_STATUS: Record<string, 'ready' | 'in_progress' | 'needs_attention'> = {}

const STATUS_MAP = {
  ready:           { label: 'Ready',           className: 'bg-green-100 text-green-700',  icon: CheckCircle },
  in_progress:     { label: 'In Progress',     className: 'bg-blue-100 text-blue-700',    icon: Loader2 },
  needs_attention: { label: 'Needs Attention', className: 'bg-red-100 text-red-700',      icon: AlertTriangle },
}

const CYCLE: Array<'ready' | 'in_progress' | 'needs_attention'> = ['ready', 'in_progress', 'needs_attention']

export default function CompliancePage() {
  const { config } = useConfig()   // criteria labels come from .env → /api/config
  const [criteriaStatus, setCriteriaStatus] = useState<Record<string, 'ready' | 'in_progress' | 'needs_attention'>>(DEFAULT_STATUS)
  const [response, setResponse] = useState('')
  const [loading, setLoading]   = useState<string | null>(null)

  const criteria = config.accreditation_criteria   // { "1": "Vision Mission...", "2": "..." }
  const body     = config.accreditation_body        // NBA | NAAC | etc.

  const getStatus = (key: string) => criteriaStatus[key] ?? 'in_progress'

  const cycleStatus = (key: string) => {
    const current = getStatus(key)
    const next = CYCLE[(CYCLE.indexOf(current) + 1) % CYCLE.length]
    setCriteriaStatus((s) => ({ ...s, [key]: next }))
  }

  const readyCount = Object.keys(criteria).filter((k) => getStatus(k) === 'ready').length
  const total      = Object.keys(criteria).length || 1
  const readinessPercent = Math.round((readyCount / total) * 100)

  const QUICK_QUERIES = [
    { label: `${body} Checklist`,  query: `Generate a complete ${body} compliance checklist for the ${config.department} department with current status for each criterion.` },
    { label: 'CO-PO Analysis',     query: `Explain how to calculate CO-PO attainment for ${body} submission. What are the target levels and how are they computed?` },
    { label: 'SAR Guidance',       query: `Guide me on preparing the ${body} Self-Assessment Report (SAR). What are the key sections and evidence required per criterion?` },
    { label: 'Audit Readiness',    query: `What documents must be ready before a ${body} peer team visit? Create a pre-audit preparation checklist.` },
    { label: 'Gap Analysis',       query: `Perform a gap analysis for ${body} accreditation in the ${config.department} department. Rank gaps by severity and suggest actions.` },
    { label: 'CO Attainment',      query: `What is the standard CO attainment calculation method for ${body}? Give me a worked example for any engineering course.` },
  ]

  const runQuery = async (query: string, label: string) => {
    setLoading(label)
    try {
      const res = await agentApi.chat(query, 'nba_compliance')
      setResponse(res.data.response)
    } catch {
      toast.error('Unable to connect to AI backend')
    } finally {
      setLoading(null)
    }
  }

  return (
    <AppShell>
      <div className="space-y-5">

        {/* ── Summary Cards ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">{body} Readiness</span>
              <Shield className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{readinessPercent}%</p>
            <div className="mt-2 h-2 bg-gray-100 rounded-full">
              <div className="h-2 bg-blue-500 rounded-full transition-all" style={{ width: `${readinessPercent}%` }} />
            </div>
          </div>
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">Criteria Ready</span>
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{readyCount}/{total}</p>
            <p className="text-xs text-gray-400 mt-1">{body} criteria completed</p>
          </div>
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">Needs Attention</span>
              <AlertTriangle className="w-5 h-5 text-red-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {Object.keys(criteria).filter((k) => getStatus(k) === 'needs_attention').length}
            </p>
            <p className="text-xs text-gray-400 mt-1">Criteria need action</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

          {/* ── Criteria Status List — dynamic from config ── */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800">{body} Criteria Status</h3>
              <span className="text-xs text-gray-400">Click status to cycle</span>
            </div>
            <div className="space-y-2">
              {Object.entries(criteria).map(([key, label]) => {
                const status = getStatus(key)
                const sc = STATUS_MAP[status]
                const Icon = sc.icon
                return (
                  <div key={key} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-full bg-[#1e3a5f] text-white text-xs flex items-center justify-center font-semibold flex-shrink-0">
                        {key}
                      </span>
                      <span className="text-sm text-gray-700">{label}</span>
                    </div>
                    <button
                      onClick={() => cycleStatus(key)}
                      className={clsx('text-xs px-2 py-1 rounded-full font-medium flex items-center gap-1 cursor-pointer hover:opacity-80 transition-opacity', sc.className)}>
                      <Icon className="w-3 h-3" />
                      {sc.label}
                    </button>
                  </div>
                )
              })}
            </div>
            <p className="text-xs text-gray-400 mt-3">
              Criteria labels configured via <code className="bg-gray-100 px-1 rounded">ACCREDITATION_CRITERIA</code> in <code className="bg-gray-100 px-1 rounded">.env</code>
            </p>
          </div>

          {/* ── AI Compliance Assistant ── */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h3 className="font-semibold text-gray-800 mb-4">AI {body} Assistant</h3>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {QUICK_QUERIES.map((q) => (
                <button key={q.label}
                  onClick={() => runQuery(q.query, q.label)}
                  disabled={loading !== null}
                  className="flex items-center gap-2 px-3 py-2.5 border border-gray-200 rounded-lg text-xs text-gray-700 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 transition-all text-left disabled:opacity-60">
                  {loading === q.label
                    ? <Loader2 className="w-3 h-3 animate-spin flex-shrink-0" />
                    : <Shield className="w-3 h-3 flex-shrink-0" />}
                  {q.label}
                </button>
              ))}
            </div>

            {response ? (
              <div className="border border-gray-100 rounded-lg p-4 max-h-72 overflow-y-auto bg-gray-50">
                <div className="prose-ai">
                  <ReactMarkdown>{response}</ReactMarkdown>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-gray-400">
                <Shield className="w-8 h-8 opacity-30 mb-2" />
                <p className="text-sm">Click a button above to get AI guidance</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
