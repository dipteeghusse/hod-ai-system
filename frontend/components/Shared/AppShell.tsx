'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore, useUIStore } from '@/lib/store'
import Sidebar from './Sidebar'
import Header from './Header'
import clsx from 'clsx'

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { token } = useAuthStore()
  const { sidebarOpen } = useUIStore()

  useEffect(() => {
    if (!token) router.replace('/login')
  }, [token, router])

  if (!token) return null

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className={clsx(
        'flex-1 flex flex-col min-h-screen transition-all duration-300',
        sidebarOpen ? 'ml-60' : 'ml-16'
      )}>
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
