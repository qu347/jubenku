import { request } from './http'
import type { ModuleSection, ModuleSectionPayload, ReorderItem } from '../types/moduleSection'

export const getModuleSection = (id: string) =>
  request<ModuleSection>({ method: 'GET', url: `/module-sections/${id}` })

export const updateModuleSection = (id: string, data: Partial<ModuleSectionPayload>) =>
  request<ModuleSection>({ method: 'PATCH', url: `/module-sections/${id}`, data })

export const deleteModuleSection = (id: string) =>
  request<{ id: string }>({ method: 'DELETE', url: `/module-sections/${id}` })

export const enableModuleSection = (id: string) =>
  request<ModuleSection>({ method: 'POST', url: `/module-sections/${id}/enable` })

export const disableModuleSection = (id: string) =>
  request<ModuleSection>({ method: 'POST', url: `/module-sections/${id}/disable` })

export const reorderModuleSections = (items: ReorderItem[]) =>
  request<ModuleSection[]>({ method: 'PATCH', url: '/module-sections/batch/reorder', data: { items } })
