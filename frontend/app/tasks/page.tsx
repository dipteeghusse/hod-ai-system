'use client'

import AppShell from '@/components/Shared/AppShell'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi, facultyApi } from '@/lib/api'
import { useConfig } from '@/lib/useConfig'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Plus, CheckCircle, Clock, AlertTriangle, XCircle, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import { format } from 'date-fns'

const STATUS_CONFIG: Record<string, { label: string; icon: any; className: string }> = {
  pending:     { label: 'Pending',     icon: Clock,          className: 'status-pending' },
  in_progress: { label: 'In Progress', icon: Clock,          className: 'status-in_progress' },
  completed:   { label: 'Completed',   icon: CheckCircle,    className: 'status-completed' },
  overdue:     { label: 'Overdue',     icon: AlertTriangle,  className: 'status-overdue' },
  delayed:     { label: 'Delayed',     icon: XCircle,        className: 'status-delayed' },
}

const PRIORITY_CONFIG: Record<string, string> = {
  low: 'badge-low', medium: 'badge-medium', high: 'badge-high', critical: 'badge-critical',
}

const EMPTY_FORM = {
  title: '', description: '', priority: 'medium',
  category: '', subject: '', due_date: '', assigned_to_id: '',
}

export default function TasksPage() {
  const qc = useQueryClient()
  const { config } = useConfig()                // ← all categories/subjects from .env via API

  const [filterStatus, setFilterStatus]     = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [showCreate, setShowCreate]         = useState(false)
  const [form, setForm]                     = useState(EMPTY_FORM)

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks', filterStatus, filterPriority, filterCategory],
    queryFn: () =>
      tasksApi.list({
        status:   filterStatus   || undefined,
        priority: filterPriority || undefined,
      }).then((r) => r.data),
  })

  const { data: faculty = [] } = useQuery({
    queryKey: ['faculty'],
    queryFn: () => facultyApi.list().then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => tasksApi.create(data),
    onSuccess: () => {
      toast.success('Task created')
      qc.invalidateQueries({ queryKey: ['tasks'] })
      setShowCreate(false)
      setForm(EMPTY_FORM)
    },
    onError: () => toast.error('Failed to create task'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => tasksApi.update(id, data),
    onSuccess: () => {
      toast.success('Task updated')
      qc.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      ...form,
      assigned_to_id: form.assigned_to_id ? parseInt(form.assigned_to_id) : null,
      due_date: new Date(form.due_date).toISOString(),
      category: form.category || config.task_categories[0] || 'general',
    })
  }

  // Client-side category filter
  const filtered = filterCategory
    ? (tasks as any[]).filter((t: any) => t.category === filterCategory)
    : (tasks as any[])

  return (
    <AppShell>
      <div className="space-y-5">

        {/* ── Toolbar ── */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Status filter */}
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">All Status</option>
            {Object.entries(STATUS_CONFIG).map(([k, v]) =>
              <option key={k} value={k}>{v.label}</option>)}
          </select>

          {/* Priority filter */}
          <select value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">All Priorities</option>
            {['low', 'medium', 'high', 'critical'].map((p) =>
              <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
          </select>

          {/* Category filter — loaded from config */}
          <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">All Categories</option>
            {config.task_categories.map((c) =>
              <option key={c} value={c}>{c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
          </select>

          <div className="flex-1" />
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[#1e3a5f] text-white rounded-lg text-sm font-medium hover:bg-[#1e4d8c] transition-colors">
            <Plus className="w-4 h-4" /> New Task
          </button>
        </div>

        {/* ── Create Task Modal ── */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-5 border-b border-gray-100 sticky top-0 bg-white">
                <h2 className="text-lg font-semibold text-gray-900">Create New Task</h2>
              </div>

              <form onSubmit={handleCreate} className="px-6 py-5 space-y-4">
                {/* Title */}
                <input required placeholder="Task title *" value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />

                {/* Description */}
                <textarea required placeholder="Description *" rows={3} value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500" />

                {/* Subject — free text from config list */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Subject / Course <span className="text-gray-400">(optional)</span>
                  </label>
                  <input
                    list="subjects-list"
                    placeholder="Type or select a subject…"
                    value={form.subject}
                    onChange={(e) => setForm({ ...form, subject: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {/* datalist — populated from config */}
                  <datalist id="subjects-list">
                    {config.subjects.map((s) => <option key={s} value={s} />)}
                  </datalist>
                </div>

                {/* Priority + Category */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Priority</label>
                    <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}
                      className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      {['low', 'medium', 'high', 'critical'].map((p) =>
                        <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Category</label>
                    {/* Category dropdown — driven by config from .env */}
                    <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                      className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="">Select category…</option>
                      {config.task_categories.map((c) =>
                        <option key={c} value={c}>
                          {c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </option>
                      )}
                    </select>
                  </div>
                </div>

                {/* Due Date + Assignee */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Due Date *</label>
                    <input required type="datetime-local" value={form.due_date}
                      onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                      className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Assign To</label>
                    <select value={form.assigned_to_id}
                      onChange={(e) => setForm({ ...form, assigned_to_id: e.target.value })}
                      className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="">Unassigned</option>
                      {(faculty as any[]).map((f: any) =>
                        <option key={f.id} value={f.id}>{f.name}</option>)}
                    </select>
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setShowCreate(false)}
                    className="px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
                    Cancel
                  </button>
                  <button type="submit" disabled={createMutation.isPending}
                    className="px-5 py-2 bg-[#1e3a5f] text-white rounded-lg text-sm font-medium hover:bg-[#1e4d8c] disabled:opacity-60 flex items-center gap-2">
                    {createMutation.isPending && <Loader2 className="w-3 h-3 animate-spin" />}
                    Create Task
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ── Task Table ── */}
        {isLoading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center text-gray-400 shadow-sm border border-gray-100">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No tasks found</p>
            <p className="text-sm mt-1">Create a task or adjust filters</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[800px]">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    {['Title', 'Subject', 'Category', 'Priority', 'Status', 'Assigned To', 'Due Date', 'Progress', 'Action'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {filtered.map((task: any) => {
                    const sc = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending
                    return (
                      <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 max-w-[200px]">
                          <p className="font-medium text-gray-900 truncate">{task.title}</p>
                        </td>
                        <td className="px-4 py-3 text-gray-500 text-xs">
                          {task.subject || '—'}
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full capitalize">
                            {(task.category || '').replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={clsx('text-xs px-2 py-1 rounded-full font-medium capitalize', PRIORITY_CONFIG[task.priority])}>
                            {task.priority}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={clsx('text-xs px-2 py-1 rounded-full font-medium', sc.className)}>
                            {sc.label}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                          {task.assigned_to_name || '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                          {format(new Date(task.due_date), 'MMM d, yyyy')}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 min-w-[80px]">
                            <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                              <div className="bg-blue-500 h-1.5 rounded-full"
                                style={{ width: `${task.progress_percentage}%` }} />
                            </div>
                            <span className="text-xs text-gray-500 w-8">{task.progress_percentage}%</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <select value={task.status}
                            onChange={(e) => updateMutation.mutate({ id: task.id, data: { status: e.target.value } })}
                            className="text-xs border border-gray-200 rounded px-2 py-1 bg-white focus:outline-none">
                            {Object.entries(STATUS_CONFIG).map(([s, sc]) =>
                              <option key={s} value={s}>{sc.label}</option>)}
                          </select>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}
