'use client'

import AppShell from '@/components/Shared/AppShell'
import { useState, useRef, useEffect } from 'react'
import { agentApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import ReactMarkdown from 'react-markdown'
import {
  Send, Loader2, Bot, User, Trash2, ChevronDown
} from 'lucide-react'
import clsx from 'clsx'

const AGENTS = [
  { value: 'hod_assistant', label: '🎓 HoD Assistant', desc: 'Daily briefings & priorities' },
  { value: 'task_planner', label: '📋 Task Planner', desc: 'Create task plans' },
  { value: 'task_allocator', label: '👥 Task Allocator', desc: 'Assign tasks to faculty' },
  { value: 'progress_tracker', label: '📊 Progress Tracker', desc: 'Track completion status' },
  { value: 'meeting_manager', label: '📅 Meeting Manager', desc: 'Agenda & MoM' },
  { value: 'email_intelligence', label: '✉️ Email Intelligence', desc: 'Analyze & draft emails' },
  { value: 'nba_compliance', label: '🛡️ NBA/NAAC Agent', desc: 'Compliance tracking' },
  { value: 'report_generator', label: '📄 Report Generator', desc: 'Generate reports' },
]

const QUICK_PROMPTS = [
  "What are my top priorities today?",
  "Generate a weekly task plan for the department",
  "Summarize the current task completion status",
  "Create an agenda for the next department meeting",
  "Check NBA compliance readiness for the department",
  "Which faculty are overloaded with tasks?",
  "Generate a monthly department report",
  "What activities are overdue this week?",
]

interface Message {
  role: 'user' | 'assistant'
  content: string
  agent?: string
  timestamp: Date
}

export default function ChatPage() {
  const { user } = useAuthStore()
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `# Welcome to HOD AI Assistant! 👋

I'm your intelligent department management assistant for **MITAOE CSE (AI & ML)**. I can help you with:

- **Daily Planning** — priorities, briefings, calendar
- **Task Management** — create, assign, track tasks
- **Meeting Management** — agenda, minutes, action items
- **Faculty Coordination** — workload, performance, activities
- **NBA/NAAC Compliance** — documentation, CO-PO attainment
- **Report Generation** — weekly, monthly, semester reports

Select an agent from the dropdown and ask me anything!`,
      agent: 'hod_assistant',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState('hod_assistant')
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const [showAgentPicker, setShowAgentPicker] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text?: string) => {
    const query = text || input.trim()
    if (!query || loading) return

    setInput('')
    setMessages((m) => [...m, { role: 'user', content: query, timestamp: new Date() }])
    setLoading(true)

    try {
      const res = await agentApi.chat(query, selectedAgent, {}, sessionId)
      const data = res.data
      setMessages((m) => [...m, {
        role: 'assistant',
        content: data.response,
        agent: data.agent_type,
        timestamp: new Date(),
      }])
    } catch (err: any) {
      setMessages((m) => [...m, {
        role: 'assistant',
        content: '⚠️ **Connection Error** — The AI backend is not reachable. Please ensure the FastAPI server is running on port 8000.',
        agent: selectedAgent,
        timestamp: new Date(),
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const activeAgent = AGENTS.find((a) => a.value === selectedAgent)!

  return (
    <AppShell>
      <div className="h-[calc(100vh-8rem)] flex gap-5">
        {/* Main chat */}
        <div className="flex-1 flex flex-col bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          {/* Agent selector bar */}
          <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
            <div className="relative">
              <button onClick={() => setShowAgentPicker(!showAgentPicker)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                <Bot className="w-4 h-4 text-blue-600" />
                <span>{activeAgent.label}</span>
                <ChevronDown className={clsx('w-4 h-4 text-gray-400 transition-transform', showAgentPicker && 'rotate-180')} />
              </button>
              {showAgentPicker && (
                <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 w-72 py-1">
                  {AGENTS.map((a) => (
                    <button key={a.value}
                      onClick={() => { setSelectedAgent(a.value); setShowAgentPicker(false) }}
                      className={clsx(
                        'w-full text-left px-4 py-2.5 hover:bg-gray-50 transition-colors',
                        selectedAgent === a.value && 'bg-blue-50'
                      )}>
                      <p className="text-sm font-medium text-gray-800">{a.label}</p>
                      <p className="text-xs text-gray-500">{a.desc}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button onClick={() => setMessages(messages.slice(0, 1))}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={clsx('flex gap-3', msg.role === 'user' && 'flex-row-reverse')}>
                {/* Avatar */}
                <div className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm',
                  msg.role === 'user' ? 'bg-[#1e3a5f] text-white' : 'bg-amber-100 text-amber-700'
                )}>
                  {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Bubble */}
                <div className={clsx(
                  'max-w-[78%] rounded-xl px-4 py-3 text-sm',
                  msg.role === 'user'
                    ? 'bg-[#1e3a5f] text-white rounded-tr-none'
                    : 'bg-gray-50 border border-gray-100 text-gray-800 rounded-tl-none'
                )}>
                  {msg.role === 'assistant' ? (
                    <div className="prose-ai">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p>{msg.content}</p>
                  )}
                  <div className={clsx('text-[10px] mt-2 flex items-center gap-2', msg.role === 'user' ? 'text-blue-200 justify-end' : 'text-gray-400')}>
                    {msg.agent && <span className="capitalize">via {msg.agent.replace('_', ' ')}</span>}
                    <span>{msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-amber-700" />
                </div>
                <div className="bg-gray-50 border border-gray-100 rounded-xl rounded-tl-none px-4 py-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                  <span className="text-sm text-gray-500">AI is thinking...</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="px-5 py-4 border-t border-gray-100">
            <div className="flex gap-2 items-end">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Ask ${activeAgent.label}...`}
                rows={2}
                className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button onClick={() => send()} disabled={!input.trim() || loading}
                className="p-3 bg-[#1e3a5f] text-white rounded-xl hover:bg-[#1e4d8c] disabled:opacity-50 transition-colors flex-shrink-0">
                <Send className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-1.5">Press Enter to send · Shift+Enter for new line</p>
          </div>
        </div>

        {/* Quick prompts sidebar */}
        <div className="w-64 flex-shrink-0 bg-white rounded-xl shadow-sm border border-gray-100 p-4 overflow-y-auto">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Prompts</h3>
          <div className="space-y-2">
            {QUICK_PROMPTS.map((p) => (
              <button key={p} onClick={() => send(p)}
                className="w-full text-left px-3 py-2.5 text-xs text-gray-600 border border-gray-100 rounded-lg hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700 transition-all leading-relaxed">
                {p}
              </button>
            ))}
          </div>
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Active Agent</h3>
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-sm font-medium text-blue-800">{activeAgent.label}</p>
              <p className="text-xs text-blue-600 mt-1">{activeAgent.desc}</p>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
