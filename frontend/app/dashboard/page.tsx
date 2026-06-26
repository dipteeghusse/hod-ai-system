'use client'

import AppShell from '@/components/Shared/AppShell'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi, agentApi } from '@/lib/api'
import {
  CheckSquare, Clock, AlertTriangle, Users, Calendar,
  TrendingUp, Zap, RefreshCw, Bell, ArrowRight
} from 'lucide-react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useState } from 'react'
import clsx from 'clsx'
import ReactMarkdown from 'react-markdown'

const PIE_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6']

export default function DashboardPage() {
  const { data: statsData, isLoading, refetch } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.stats().then((r) => r.data),
    refetchInterval: 60_000,
  })

  const [briefing, setBriefing] = useState<string>('')
  const [briefingLoading, setBriefingLoading] = useState(false)

  const { data: digestData } = useQuery({
    queryKey: ['followup-digest'],
    queryFn: () => api.get('/followup/digest').then(r => r.data),
    refetchInterval: 5 * 60_000,
    staleTime: 2 * 60_000,
  })

  const stats = statsData

  const handleMorningBriefing = async () => {
    setBriefingLoading(true)
    try {
      const res = await agentApi.chat(
        'Give me a concise morning briefing with today\'s priorities, overdue tasks, and key action items.',
        'hod_assistant'
      )
      setBriefing(res.data.response)
    } catch {
      setBriefing('Unable to connect to AI assistant. Please check the backend server.')
    } finally {
      setBriefingLoading(false)
    }
  }

  const statCards = [
    { label: 'Total Tasks', value: stats?.total_tasks ?? 0, icon: CheckSquare, color: 'blue', bg: 'bg-blue-50', iconColor: 'text-blue-600' },
    { label: 'Pending', value: stats?.pending_tasks ?? 0, icon: Clock, color: 'yellow', bg: 'bg-amber-50', iconColor: 'text-amber-600' },
    { label: 'Overdue', value: stats?.overdue_tasks ?? 0, icon: AlertTriangle, color: 'red', bg: 'bg-red-50', iconColor: 'text-red-600' },
    { label: 'Faculty', value: stats?.faculty_count ?? 0, icon: Users, color: 'purple', bg: 'bg-purple-50', iconColor: 'text-purple-600' },
    { label: 'Today\'s Meetings', value: stats?.upcoming_meetings ?? 0, icon: Calendar, color: 'green', bg: 'bg-green-50', iconColor: 'text-green-600' },
    { label: 'Completion Rate', value: `${stats?.completion_rate ?? 0}%`, icon: TrendingUp, color: 'teal', bg: 'bg-teal-50', iconColor: 'text-teal-600' },
  ]

  const priorityData = Object.entries(stats?.task_by_priority ?? {}).map(([k, v]) => ({
    name: k.charAt(0).toUpperCase() + k.slice(1), value: v as number
  }))

  const statusData = [
    { name: 'Pending', value: stats?.pending_tasks ?? 0 },
    { name: 'In Progress', value: stats?.in_progress_tasks ?? 0 },
    { name: 'Completed', value: stats?.completed_tasks ?? 0 },
    { name: 'Overdue', value: stats?.overdue_tasks ?? 0 },
  ]

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Top bar */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Department Overview</h2>
            <p className="text-sm text-gray-500">CSE (AI & ML) · MITAOE · 2025-26</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => refetch()}
              className="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors">
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button onClick={handleMorningBriefing} disabled={briefingLoading}
              className="flex items-center gap-2 px-4 py-2 bg-[#1e3a5f] text-white rounded-lg text-sm font-medium hover:bg-[#1e4d8c] transition-colors disabled:opacity-60">
              <Zap className="w-4 h-4" />
              {briefingLoading ? 'Generating...' : 'AI Briefing'}
            </button>
          </div>
        </div>

        {/* AI Morning Briefing */}
        {briefing && (
          <div className="bg-gradient-to-r from-[#1e3a5f] to-[#1e4d8c] rounded-xl p-5 text-white">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-5 h-5 text-amber-400" />
              <h3 className="font-semibold text-sm">AI Morning Briefing</h3>
            </div>
            <div className="text-sm text-blue-100 leading-relaxed prose-ai">
              <ReactMarkdown>{briefing}</ReactMarkdown>
            </div>
          </div>
        )}

        {/* Follow-Up Digest Banner */}
        {digestData && (digestData.counts?.overdue > 0 || digestData.counts?.at_risk > 0) && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-start gap-4">
            <div className="flex items-center gap-2 text-amber-700 shrink-0">
              <Bell className="w-5 h-5" />
              <span className="font-semibold text-sm">Follow-Up Alert</span>
            </div>
            <div className="flex-1 text-sm text-amber-900 leading-relaxed whitespace-pre-wrap">
              {digestData.digest}
            </div>
            <Link href="/followup"
              className="shrink-0 flex items-center gap-1 text-xs font-medium text-amber-700 hover:text-amber-900 border border-amber-300 px-3 py-1.5 rounded-lg hover:bg-amber-100 transition">
              Full Report <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}

        {/* Stat Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {statCards.map(({ label, value, icon: Icon, bg, iconColor }) => (
            <div key={label} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className={clsx('w-9 h-9 rounded-lg flex items-center justify-center mb-3', bg)}>
                <Icon className={clsx('w-5 h-5', iconColor)} />
              </div>
              <p className="text-2xl font-bold text-gray-900">{isLoading ? '—' : value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Status Bar Chart */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-800 mb-4">Task Status Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={statusData}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Priority Pie Chart */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-800 mb-4">Tasks by Priority</h3>
            {priorityData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={priorityData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                    {priorityData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
                No task data available
              </div>
            )}
          </div>
        </div>

        {/* Recent AI Activity */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">Recent AI Activity</h3>
          {stats?.recent_activities?.length ? (
            <div className="space-y-2">
              {stats.recent_activities.map((a: any, i: number) => (
                <div key={i} className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0">
                  <div className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 truncate">{a.query}</p>
                    <p className="text-xs text-gray-400">{a.agent} · {new Date(a.time).toLocaleTimeString()}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center py-8">
              No AI activity yet. Start a conversation with the AI Assistant.
            </p>
          )}
        </div>
      </div>
    </AppShell>
  )
}
