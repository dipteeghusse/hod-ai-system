'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuthStore, useUIStore } from '@/lib/store'
import {
  LayoutDashboard, CheckSquare, Users, Calendar, MessageSquare,
  FileText, Shield, BarChart3, LogOut, ChevronLeft, GraduationCap, Bot
} from 'lucide-react'
import clsx from 'clsx'

const nav = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Tasks', href: '/tasks', icon: CheckSquare },
  { label: 'Faculty', href: '/faculty', icon: Users },
  { label: 'Meetings', href: '/meetings', icon: Calendar },
  { label: 'AI Assistant', href: '/chat', icon: Bot },
  { label: 'Reports', href: '/reports', icon: FileText },
  { label: 'NBA/NAAC', href: '/compliance', icon: Shield },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuthStore()
  const { sidebarOpen, toggleSidebar } = useUIStore()

  return (
    <aside className={clsx(
      'fixed left-0 top-0 h-full bg-[#1e3a5f] text-white flex flex-col transition-all duration-300 z-40 shadow-xl',
      sidebarOpen ? 'w-60' : 'w-16'
    )}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10">
        <div className="w-8 h-8 bg-amber-400 rounded-lg flex items-center justify-center flex-shrink-0">
          <GraduationCap className="w-5 h-5 text-[#1e3a5f]" />
        </div>
        {sidebarOpen && (
          <div className="min-w-0">
            <p className="font-bold text-sm truncate">HOD AI System</p>
            <p className="text-[10px] text-blue-300 truncate">CSE-AIML · MITAOE</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 overflow-y-auto">
        {nav.map(({ label, href, icon: Icon }) => {
          const active = pathname.startsWith(href)
          return (
            <Link key={href} href={href}
              className={clsx(
                'flex items-center gap-3 px-4 py-3 mx-2 rounded-lg text-sm font-medium transition-all mb-1',
                active ? 'bg-white/15 text-white' : 'text-blue-200 hover:bg-white/10 hover:text-white'
              )}>
              <Icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span>{label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* User + Collapse */}
      <div className="border-t border-white/10 p-3 space-y-1">
        {sidebarOpen && user && (
          <div className="flex items-center gap-2 px-2 py-2">
            <div className="w-8 h-8 rounded-full bg-amber-400 flex items-center justify-center flex-shrink-0">
              <span className="text-[#1e3a5f] text-xs font-bold">
                {user.name.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium truncate">{user.name}</p>
              <p className="text-[10px] text-blue-300 capitalize">{user.role}</p>
            </div>
          </div>
        )}
        <button onClick={logout}
          className="flex items-center gap-3 w-full px-4 py-2 rounded-lg text-red-300 hover:bg-red-500/20 hover:text-red-200 text-sm transition-all">
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {sidebarOpen && <span>Logout</span>}
        </button>
        <button onClick={toggleSidebar}
          className="flex items-center gap-3 w-full px-4 py-2 rounded-lg text-blue-300 hover:bg-white/10 text-sm transition-all">
          <ChevronLeft className={clsx('w-4 h-4 flex-shrink-0 transition-transform', !sidebarOpen && 'rotate-180')} />
          {sidebarOpen && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  )
}
