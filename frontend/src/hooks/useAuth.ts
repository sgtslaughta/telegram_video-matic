import { useMutation } from '@tanstack/react-query'
import * as api from '@/lib/api'

export function useLogin() {
  return useMutation({
    mutationFn: (password: string) => api.auth.login(password),
  })
}
