'use client'

import AppShell from '@/components/Shared/AppShell'
import { useQuery } from '@tanstack/react-query'
import { facultyApi, agentApi } from '@/lib/api'
import { useState } from 'react'
import { Users, TrendingUp, BookOpen, Award, Loader2, Bot } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'

export default function FacultyPage() {
  const { data: faculty = [], isLoading } = useQuery({
    queryKey: ['faculty'],
    queryFn: () => facultyApi.list().then((r) => r.data),
  })

  const [analysis, setAnalysis] = useState<string>('')
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [selectedFaculty, setSelectedFaculty] = useState<any>(null)

  const analyzeWorkload = async () => {
    setAnalysisLoading(true)
    try {
      const res = await agentApi.chat(
        `Analyze the workload and performance of the faculty team. Provide recommendations for workload balancing and highlight top performers. Faculty data: ${JSON.stringify(faculty)}`,
        'progress_tracker'
      )
      setAnalysis(res.data.response)
    } catch {
      setAnalysis('Unable to connect to AI backend.')
    } finally {
      setAnalysisLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50'
    if (score >= 60) return 'text-amber-600 bg-amber-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Faculty Management</h2>
            <p className="text-sm text-gray-500">{(faculty as any[]).length} faculty members · CSE (AI & ML)</p>
          </div>
          <button onClick={analyzeWorkload} disabled={analysisLoading}
            className="flex items-center gap-2 px-4 py-2 bg-[#1e3a5f] text-white rounded-lg text-sm font-medium hover:bg-[#1e4d8c] disabled:opacity-60 transition-colors">
            <Bot className="w-4 h-4" />
            {analysisLoading ? 'Analyzing...' : 'AI Workload Analysis'}
          </button>
        </div>

        {/* AI Analysis */}
        {analysis && (
          <div className="bg-white rounded-xl p-5 shadow-sm border border-blue-100">
            <div className="flex items-center gap-2 mb-3">
              <Bot className="w-4 h-4 text-blue-600" />
              <h3 className="font-semibold text-gray-800 text-sm">AI Workload Analysis</h3>
            </div>
            <div className="prose-ai">
              <ReactMarkdown>{analysis}</ReactMarkdown>
            </div>
          </div>
        )}

        {/* Faculty Grid */}
        {isLoading ? (
          <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-gray-400" /></div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {(faculty as any[]).map((f: any) => (
              <div key={f.id}
                className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedFaculty(selectedFaculty?.id === f.id ? null : f)}>
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-[#1e3a5f] flex items-center justify-center">
                      <span className="text-white font-bold text-sm">{f.name.charAt(0)}</span>
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 text-sm">{f.name}</p>
                      <p className="text-xs text-gray-500">{f.designation}</p>
                    </div>
                  </div>
                  <span className={clsx('text-xs font-semibold px-2 py-1 rounded-full', getScoreColor(f.performance_score))}>
                    {f.performance_score}%
                  </span>
                </div>

                {/* Specialization */}
                <div className="flex flex-wrap gap-1 mb-4">
                  {(f.specialization || []).map((s: string) => (
                    <span key={s} className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">{s}</span>
                  ))}
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-center p-2 bg-gray-50 rounded-lg">
                    <p className="text-base font-bold text-gray-900">{f.total_tasks}</p>
                    <p className="text-[10px] text-gray-500">Total</p>
                  </div>
                  <div className="text-center p-2 bg-green-50 rounded-lg">
                    <p className="text-base font-bold text-green-700">{f.completed_tasks}</p>
                    <p className="text-[10px] text-gray-500">Done</p>
                  </div>
                  <div className="text-center p-2 bg-amber-50 rounded-lg">
                    <p className="text-base font-bold text-amber-700">{f.pending_tasks}</p>
                    <p className="text-[10px] text-gray-500">Pending</p>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Task Completion</span>
                    <span>{f.performance_score}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={clsx('h-full rounded-full', f.performance_score >= 80 ? 'bg-green-500' : f.performance_score >= 60 ? 'bg-amber-500' : 'bg-red-500')}
                      style={{ width: `${f.performance_score}%` }}
                    />
                  </div>
                </div>

                {/* Expanded */}
                {selectedFaculty?.id === f.id && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs text-gray-500">Email: <span className="text-gray-700">{f.email}</span></p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {(faculty as any[]).length === 0 && !isLoading && (
          <div className="bg-white rounded-xl p-12 text-center text-gray-400 shadow-sm border border-gray-100">
            <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No faculty data available. Backend may not be connected.</p>
          </div>
        )}
      </div>
    </AppShell>
  )
}
