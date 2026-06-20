import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'
import type * as T from '@/lib/types'

export const tgKeys = {
  status: () => ['tg', 'status'] as const,
}

export function useTgStatus() {
  return useQuery({
    queryKey: tgKeys.status(),
    queryFn: () => api.tg.status(),
    refetchInterval: 5000, // poll every 5s as fallback
  })
}

export function useTgLoginPhone() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (phone: string) => api.tg.loginPhone(phone),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tgKeys.status() })
    },
  })
}

export function useTgLoginCode() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (code: string) => api.tg.loginCode(code),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tgKeys.status() })
    },
  })
}

export function useTgLoginPassword() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (password: string) => api.tg.loginPassword(password),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tgKeys.status() })
    },
  })
}

export function useTgLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.tg.logout(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tgKeys.status() })
    },
  })
}
