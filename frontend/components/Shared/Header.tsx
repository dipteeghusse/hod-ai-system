'use client'

import { usePathname } from 'next/navigation'
import { useUIStore, useAuthStore } from '@/lib/store'
import { Bell, Menu, Search } from 'lucide-react'
import { format } from 'date-fns'

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': { title: 'HoD Dashboard', subtitle: 'Overview of department activities' },
  '/tasks': { title: 'Task Management', subtitle: 'Assign, track, and manage department tasks' },
  '/faculty': { title: 'Faculty Management', subtitle: 'Performance tracking and coordination' },
  '/meetings': { title: 'Meeting Management', subtitle: 'Schedule, agenda, and MoM' },
  '/chat': { title: 'AI Assistant', subtitle: 'Powered by LangGraph + Groq' },
  '/reports': { title: 'Reports', subtitle: 'Auto-generated department reports' },
  '/compliance': { title: 'NBA/NAAC Compliance', subtitle: 'Accreditation tracking and readiness' },
}

export default function Header() {
  const pathname = usePathname()
  const { toggleSidebar, sidebarOpen } = useUIStore()
  const { user } = useAuthStore()

  const page = Object.entries(pageTitles).find(([k]) => pathname.startsWith(k))
  const { title, subtitle } = page?.[1] ?? { title: 'HOD AI System', subtitle: '' }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-30 shadow-sm">
      <div className="flex items-center gap-4">
        <button onClick={toggleSidebar}
          className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors lg:hidden">
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-500 hidden sm:block">
          {format(new Date(), 'EEEE, MMMM d, yyyy')}
        </span>
        <button className="relative p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
        {user && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-[#1e3a5f] flex items-center justify-center">
              <span className="text-white text-xs font-bold">{user.name.charAt(0)}</span>
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-medium text-gray-900 leading-tight">{user.name}</p>
              <p className="text-[10px] text-gray-500 capitalize">{user.role}</p>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
