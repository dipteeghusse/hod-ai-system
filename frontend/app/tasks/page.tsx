'use client'

import AppShell from '@/components/Shared/AppShell'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi, facultyApi } from '@/lib/api'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Plus, Filter, CheckCircle, Clock, AlertTriangle, XCircle, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import { format } from 'date-fns'

const STATUS_CONFIG: Record<string, { label: string; icon: any; className: string }> = {
  pending: { label: 'Pending', icon: Clock, className: 'status-pending' },
  in_progress: { label: 'In Progress', icon: Clock, className: 'status-in_progress' },
  completed: { label: 'Completed', icon: CheckCircle, className: 'status-completed' },
  overdue: { label: 'Overdue', icon: AlertTriangle, className: 'status-overdue' },
  delayed: { label: 'Delayed', icon: XCircle, className: 'status-delayed' },
}

const PRIORITY_CONFIG: Record<string, string> = {
  low: 'badge-low', medium: 'badge-medium', high: 'badge-high', critical: 'badge-critical'
}

export default function TasksPage() {
  const qc = useQueryClient()
  const [filterStatus, setFilterStatus] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    title: '', description: '', priority: 'medium', category: 'general',
    due_date: '', assigned_to_id: '',
  })

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks', filterStatus, filterPriority],
    queryFn: () => tasksApi.list({ status: filterStatus || undefined, priority: filterPriority || undefined }).then((r) => r.data),
  })

  const { data: faculty = [] } = useQuery({
    queryKey: ['faculty'],
    queryFn: () => facultyApi.list().then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => tasksApi.create(data),
    onSuccess: () => {
      toast.success('Task created successfully')
      qc.invalidateQueries({ queryKey: ['tasks'] })
      setShowCreate(false)
      setForm({ title: '', description: '', priority: 'medium', category: 'general', due_date: '', assigned_to_id: '' })
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
    })
  }

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">All Status</option>
            {Object.entries(STATUS_CONFIG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
          <select value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">All Priorities</option>
            {['low', 'medium', 'high', 'critical'].map((p) => <option key={p} value={p} className="capitalize">{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
          </select>
          <div className="flex-1" />
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[#1e3a5f] text-white rounded-lg text-sm font-medium hover:bg-[#1e4d8c] transition-colors">
            <Plus className="w-4 h-4" />
            New Task
          </button>
        </div>

        {/* Create Task Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
              <div className="px-6 py-5 border-b border-gray-100">
                <h2 className="text-lg font-semibold text-gray-900">Create New Task</h2>
              </div>
              <form onSubmit={handleCreate} className="px-6 py-5 space-y-4">
                <input required placeholder="Task title *" value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <textarea required placeholder="Description *" rows={3} value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <div className="grid grid-cols-2 gap-3">
                  <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}
                    className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    {['low', 'medium', 'high', 'critical'].map((p) => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
                  </select>
                  <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                    className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    {['general', 'academic', 'research', 'administrative', 'nba', 'events', 'examination'].map((c) => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input required type="datetime-local" value={form.due_date}
                    onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                    className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  <select value={form.assigned_to_id} onChange={(e) => setForm({ ...form, assigned_to_id: e.target.value })}
                    className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">Assign to...</option>
                    {(faculty as any[]).map((f: any) => <option key={f.id} value={f.id}>{f.name}</option>)}
                  </select>
                </div>
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setShowCreate(false)}
                    className="px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
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

        {/* Task List */}
        {isLoading ? (
          <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-gray-400" /></div>
        ) : tasks.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center text-gray-400 shadow-sm border border-gray-100">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No tasks found</p>
            <p className="text-sm mt-1">Create your first task or adjust filters</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Title', 'Priority', 'Status', 'Assigned To', 'Due Date', 'Progress', 'Action'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {(tasks as any[]).map((task: any) => {
                  const sc = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending
                  return (
                    <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium text-gray-900 truncate max-w-xs">{task.title}</p>
                          <p className="text-xs text-gray-400 capitalize">{task.category}</p>
                        </div>
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
                      <td className="px-4 py-3 text-gray-600">{task.assigned_to_name || '—'}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {format(new Date(task.due_date), 'MMM d, yyyy')}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                            <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${task.progress_percentage}%` }} />
                          </div>
                          <span className="text-xs text-gray-500 w-8">{task.progress_percentage}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <select value={task.status}
                          onChange={(e) => updateMutation.mutate({ id: task.id, data: { status: e.target.value } })}
                          className="text-xs border border-gray-200 rounded px-2 py-1 bg-white focus:outline-none">
                          {Object.keys(STATUS_CONFIG).map((s) => <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>)}
                        </select>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  )
}
