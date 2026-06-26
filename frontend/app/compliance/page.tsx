'use client'

import AppShell from '@/components/Shared/AppShell'
import { agentApi } from '@/lib/api'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Shield, CheckCircle, AlertTriangle, Loader2, Zap } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'

const NBA_CRITERIA = [
  { no: '1', title: 'Vision, Mission & PEOs', status: 'ready' },
  { no: '2', title: 'Program Outcomes & COs', status: 'in_progress' },
  { no: '3', title: 'Curriculum & Teaching', status: 'ready' },
  { no: '4', title: 'Students\' Performance', status: 'in_progress' },
  { no: '5', title: 'Faculty Contributions', status: 'needs_attention' },
  { no: '6', title: 'Facilities & Technical Support', status: 'ready' },
  { no: '7', title: 'Continuous Improvement', status: 'in_progress' },
  { no: '8', title: 'First Year Academics', status: 'ready' },
]

const STATUS_MAP = {
  ready: { label: 'Ready', className: 'bg-green-100 text-green-700', icon: CheckCircle },
  in_progress: { label: 'In Progress', className: 'bg-blue-100 text-blue-700', icon: Loader2 },
  needs_attention: { label: 'Needs Attention', className: 'bg-red-100 text-red-700', icon: AlertTriangle },
}

const COMPLIANCE_PROMPTS = [
  { label: 'NBA Checklist', query: 'Generate a complete NBA compliance checklist for CSE-AIML department with current status', icon: '📋' },
  { label: 'CO-PO Analysis', query: 'Explain how to calculate CO-PO attainment for NBA submission. What are the target levels?', icon: '📊' },
  { label: 'SAR Guidance', query: 'Guide me on preparing the NBA Self-Assessment Report (SAR). What are the key sections and evidence required?', icon: '📝' },
  { label: 'Audit Readiness', query: 'What documents must be ready before an NBA peer team visit? Create a pre-audit checklist.', icon: '✅' },
  { label: 'NAAC Criteria', query: 'List all NAAC criteria and key indicators relevant for CSE-AIML department with action items.', icon: '🏛️' },
  { label: 'Gap Analysis', query: 'Perform a gap analysis for NBA accreditation and identify the top 5 areas needing immediate attention.', icon: '🔍' },
]

export default function CompliancePage() {
  const [response, setResponse] = useState<string>('')
  const [loading, setLoading] = useState<string | null>(null)

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

  const readyCount = NBA_CRITERIA.filter((c) => c.status === 'ready').length
  const readinessPercent = Math.round((readyCount / NBA_CRITERIA.length) * 100)

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">NBA Readiness</span>
              <Shield className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{readinessPercent}%</p>
            <div className="mt-2 h-2 bg-gray-100 rounded-full">
              <div className="h-2 bg-blue-500 rounded-full" style={{ width: `${readinessPercent}%` }} />
            </div>
          </div>
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">Criteria Ready</span>
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{readyCount}/{NBA_CRITERIA.length}</p>
            <p className="text-xs text-gray-400 mt-1">NBA criteria completed</p>
          </div>
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">Needs Attention</span>
              <AlertTriangle className="w-5 h-5 text-red-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{NBA_CRITERIA.filter(c => c.status === 'needs_attention').length}</p>
            <p className="text-xs text-gray-400 mt-1">Criteria need action</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* NBA Criteria Status */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h3 className="font-semibold text-gray-800 mb-4">NBA Criteria Status</h3>
            <div className="space-y-2">
              {NBA_CRITERIA.map((c) => {
                const sc = STATUS_MAP[c.status as keyof typeof STATUS_MAP]
                const Icon = sc.icon
                return (
                  <div key={c.no} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-full bg-[#1e3a5f] text-white text-xs flex items-center justify-center font-semibold flex-shrink-0">
                        {c.no}
                      </span>
                      <span className="text-sm text-gray-700">{c.title}</span>
                    </div>
                    <span className={clsx('text-xs px-2 py-1 rounded-full font-medium flex items-center gap-1', sc.className)}>
                      <Icon className="w-3 h-3" />
                      {sc.label}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* AI Compliance Assistant */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h3 className="font-semibold text-gray-800 mb-4">AI Compliance Assistant</h3>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {COMPLIANCE_PROMPTS.map((p) => (
                <button key={p.label}
                  onClick={() => runQuery(p.query, p.label)}
                  disabled={loading !== null}
                  className="flex items-center gap-2 px-3 py-2.5 border border-gray-200 rounded-lg text-xs text-gray-700 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 transition-all text-left disabled:opacity-60">
                  {loading === p.label ? <Loader2 className="w-3 h-3 animate-spin" /> : <span>{p.icon}</span>}
                  {p.label}
                </button>
              ))}
            </div>

            {response && (
              <div className="border border-gray-100 rounded-lg p-4 max-h-72 overflow-y-auto bg-gray-50">
                <div className="prose-ai">
                  <ReactMarkdown>{response}</ReactMarkdown>
                </div>
              </div>
            )}

            {!response && (
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
