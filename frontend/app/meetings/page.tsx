'use client'

import AppShell from '@/components/Shared/AppShell'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { meetingsApi } from '@/lib/api'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Plus, Calendar, Clock, MapPin, FileText, Loader2, Zap } from 'lucide-react'
import { format } from 'date-fns'
import clsx from 'clsx'
import ReactMarkdown from 'react-markdown'

const STATUS_COLORS: Record<string, string> = {
  scheduled: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-amber-100 text-amber-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-gray-100 text-gray-600',
}

export default function MeetingsPage() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [generatedAgenda, setGeneratedAgenda] = useState<{ id: number; text: string } | null>(null)
  const [form, setForm] = useState({
    title: '', description: '', scheduled_at: '', duration_minutes: 60,
    location: 'Department Conference Room', meeting_type: 'department',
  })

  const { data: meetings = [], isLoading } = useQuery({
    queryKey: ['meetings'],
    queryFn: () => meetingsApi.list().then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => meetingsApi.create(data),
    onSuccess: () => {
      toast.success('Meeting scheduled')
      qc.invalidateQueries({ queryKey: ['meetings'] })
      setShowCreate(false)
    },
    onError: () => toast.error('Failed to schedule meeting'),
  })

  const agendaMutation = useMutation({
    mutationFn: (id: number) => meetingsApi.generateAgenda(id),
    onSuccess: (res, id) => {
      setGeneratedAgenda({ id, text: res.data.agenda })
      toast.success('AI agenda generated')
    },
    onError: () => toast.error('Failed to generate agenda'),
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      ...form,
      scheduled_at: new Date(form.scheduled_at).toISOString(),
    })
  }

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Meetings</h2>
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[#1e3a5f] text-white rounded-lg text-sm font-medium hover:bg-[#1e4d8c] transition-colors">
            <Plus className="w-4 h-4" /> Schedule Meeting
          </button>
        </div>

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
              <div className="px-6 py-5 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Schedule Meeting</h2>
              </div>
              <form onSubmit={handleCreate} className="px-6 py-5 space-y-4">
                <input required placeholder="Meeting title" value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <textarea placeholder="Description" rows={2} value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <div className="grid grid-cols-2 gap-3">
                  <input required type="datetime-local" value={form.scheduled_at}
                    onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
                    className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  <input type="number" placeholder="Duration (min)" value={form.duration_minutes}
                    onChange={(e) => setForm({ ...form, duration_minutes: parseInt(e.target.value) })}
                    className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <input placeholder="Location" value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <select value={form.meeting_type} onChange={(e) => setForm({ ...form, meeting_type: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  {['department', 'faculty', 'committee', 'review', 'nba', 'emergency'].map((t) => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)} Meeting</option>
                  ))}
                </select>
                <div className="flex justify-end gap-3">
                  <button type="button" onClick={() => setShowCreate(false)}
                    className="px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
                  <button type="submit" disabled={createMutation.isPending}
                    className="px-5 py-2 bg-[#1e3a5f] text-white rounded-lg text-sm font-medium hover:bg-[#1e4d8c] disabled:opacity-60 flex items-center gap-2">
                    {createMutation.isPending && <Loader2 className="w-3 h-3 animate-spin" />}
                    Schedule
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* AI Generated Agenda */}
        {generatedAgenda && (
          <div className="bg-white rounded-xl p-5 shadow-sm border border-amber-100">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                <h3 className="font-semibold text-gray-800 text-sm">AI Generated Agenda</h3>
              </div>
              <button onClick={() => setGeneratedAgenda(null)} className="text-gray-400 hover:text-gray-600 text-xs">Dismiss</button>
            </div>
            <div className="prose-ai text-xs">
              <ReactMarkdown>{generatedAgenda.text}</ReactMarkdown>
            </div>
          </div>
        )}

        {/* Meetings List */}
        {isLoading ? (
          <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-gray-400" /></div>
        ) : (meetings as any[]).length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center text-gray-400 shadow-sm border border-gray-100">
            <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No meetings scheduled yet</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {(meetings as any[]).map((m: any) => (
              <div key={m.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">{m.title}</h3>
                      <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium capitalize', STATUS_COLORS[m.status])}>
                        {m.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mb-3">{m.description}</p>
                    <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {format(new Date(m.scheduled_at), 'MMM d, yyyy')}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {format(new Date(m.scheduled_at), 'hh:mm a')} · {m.duration_minutes} min
                      </span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5" />
                        {m.location}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => agendaMutation.mutate(m.id)}
                    disabled={agendaMutation.isPending}
                    className="flex items-center gap-1.5 px-3 py-1.5 border border-amber-200 text-amber-700 rounded-lg text-xs font-medium hover:bg-amber-50 transition-colors ml-4 flex-shrink-0 disabled:opacity-60">
                    {agendaMutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                    AI Agenda
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
