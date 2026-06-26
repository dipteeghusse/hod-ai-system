'use client'

import AppShell from '@/components/Shared/AppShell'
import { reportsApi } from '@/lib/api'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { FileText, Download, Loader2, Zap } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const REPORT_TYPES = [
  { value: 'weekly', label: 'Weekly Report', desc: 'Task completion, events, faculty activities this week', icon: '📊' },
  { value: 'monthly', label: 'Monthly Report', desc: 'Comprehensive monthly department performance', icon: '📈' },
  { value: 'semester', label: 'Semester Report', desc: 'Full semester academic and administrative summary', icon: '🎓' },
  { value: 'principal', label: 'Principal Report', desc: 'Executive-level KPI summary for Principal', icon: '🏛️' },
  { value: 'iqac', label: 'IQAC Report', desc: 'Quality assurance report for IQAC submission', icon: '✅' },
  { value: 'nba', label: 'NBA Readiness', desc: 'Accreditation compliance and gap analysis', icon: '🛡️' },
]

export default function ReportsPage() {
  const [generating, setGenerating] = useState<string | null>(null)
  const [report, setReport] = useState<{ type: string; content: string } | null>(null)

  const generateReport = async (type: string) => {
    setGenerating(type)
    try {
      const res = await reportsApi.generate(type)
      setReport({ type, content: res.data.report })
      toast.success('Report generated successfully')
    } catch {
      toast.error('Failed to generate report. Ensure backend is running.')
    } finally {
      setGenerating(null)
    }
  }

  const downloadReport = () => {
    if (!report) return
    const blob = new Blob([report.content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.type}_report_${new Date().toISOString().split('T')[0]}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <AppShell>
      <div className="space-y-5">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Report Generation</h2>
          <p className="text-sm text-gray-500">AI-powered auto-generated department reports</p>
        </div>

        {/* Report Type Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {REPORT_TYPES.map((rt) => (
            <div key={rt.value} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-3 mb-4">
                <span className="text-2xl">{rt.icon}</span>
                <div>
                  <h3 className="font-semibold text-gray-900 text-sm">{rt.label}</h3>
                  <p className="text-xs text-gray-500 mt-0.5">{rt.desc}</p>
                </div>
              </div>
              <button
                onClick={() => generateReport(rt.value)}
                disabled={generating !== null}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#1e3a5f] text-white rounded-lg text-sm font-medium hover:bg-[#1e4d8c] disabled:opacity-60 transition-colors">
                {generating === rt.value ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
                ) : (
                  <><Zap className="w-4 h-4" /> Generate</>
                )}
              </button>
            </div>
          ))}
        </div>

        {/* Generated Report */}
        {report && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-800">
                  {REPORT_TYPES.find((r) => r.value === report.type)?.label}
                </h3>
              </div>
              <button onClick={downloadReport}
                className="flex items-center gap-2 px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors">
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>
            <div className="p-5 max-h-[600px] overflow-y-auto">
              <div className="prose-ai">
                <ReactMarkdown>{report.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}
