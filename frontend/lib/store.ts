import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  name: string
  email: string
  role: 'hod' | 'faculty' | 'lab_assistant' | 'office_staff'
  department: string
}

interface AuthStore {
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => {
        set({ token: null, user: null })
        window.location.href = '/login'
      },
    }),
    { name: 'hod_auth' }
  )
)

interface UIStore {
  sidebarOpen: boolean
  activeAgent: string
  toggleSidebar: () => void
  setActiveAgent: (agent: string) => void
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: true,
  activeAgent: 'hod_assistant',
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setActiveAgent: (agent) => set({ activeAgent: agent }),
}))
