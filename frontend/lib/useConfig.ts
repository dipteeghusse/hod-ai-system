/**
 * useConfig — fetches all department configuration from the backend.
 * Dropdowns for category, subject, designation etc. are driven by this hook,
 * so nothing is hardcoded in the UI.
 */
import { useQuery } from '@tanstack/react-query'
import { api } from './api'

export interface DeptConfig {
  institution: string
  department: string
  program_level: string
  academic_year: string
  accreditation_body: string
  task_categories: string[]
  subjects: string[]
  designations: string[]
  activity_types: string[]
  accreditation_criteria: Record<string, string>
}

const DEFAULT_CONFIG: DeptConfig = {
  institution: 'My Institution',
  department: 'Department',
  program_level: 'B.Tech',
  academic_year: '2025-26',
  accreditation_body: 'NBA',
  task_categories: ['academic', 'research', 'administrative', 'examination', 'accreditation', 'events'],
  subjects: ['Subject 1', 'Subject 2', 'Subject 3'],
  designations: ['Professor', 'Associate Professor', 'Assistant Professor'],
  activity_types: ['journal_publication', 'conference_paper', 'fdp_attended', 'workshop'],
  accreditation_criteria: { '1': 'Criterion 1', '2': 'Criterion 2' },
}

export function useConfig() {
  const { data, isLoading, isError } = useQuery<DeptConfig>({
    queryKey: ['dept-config'],
    queryFn: () => api.get('/config').then((r) => r.data),
    staleTime: 5 * 60 * 1000,   // cache for 5 min
    retry: 1,
  })
  return {
    config: data ?? DEFAULT_CONFIG,
    isLoading,
    isError,
  }
}
