'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'

export default function Home() {
  const router = useRouter()
  const { token } = useAuthStore()

  useEffect(() => {
    router.replace(token ? '/dashboard' : '/login')
  }, [token, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-mitaoe-blue">
      <div className="text-center text-white">
        <div className="text-5xl mb-4">🎓</div>
        <p className="text-lg opacity-75">Loading HOD AI System...</p>
      </div>
    </div>
  )
}
