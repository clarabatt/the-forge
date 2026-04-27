import type { Application } from '@/stores/applications'

export function getAppTitle(app: Pick<Application, 'status' | 'company_name'>): string {
  return app.status === 'FAILED' ? 'Error analyzing' : app.company_name
}
