import { toast } from 'sonner'

/** Run an action with consistent toasts. Errors stay until dismissed and show
 * the server's message; successes auto-close after 4s. */
export async function withToast<T>(
  run: () => Promise<T>,
  msgs: { success: string; error?: string; undo?: () => Promise<unknown> | void },
): Promise<T | undefined> {
  try {
    const out = await run()
    toast.success(msgs.success, {
      duration: 4000,
      action: msgs.undo ? { label: 'Undo', onClick: () => void msgs.undo?.() } : undefined,
    })
    return out
  } catch (e) {
    toast.error(msgs.error ?? 'That didn’t work', {
      description: e instanceof Error ? e.message : String(e),
      duration: Infinity,
    })
    return undefined
  }
}

/** One updating toast for bursts of live events ("3 downloads finished"). */
const bursts = new Map<string, { n: number; timer?: ReturnType<typeof setTimeout> }>()
export function burstToast(key: string, one: (label: string) => string, many: (n: number) => string, label: string) {
  const b = bursts.get(key) ?? { n: 0 }
  b.n += 1
  clearTimeout(b.timer)
  b.timer = setTimeout(() => bursts.delete(key), 8000)
  bursts.set(key, b)
  toast.success(b.n === 1 ? one(label) : many(b.n), { id: `burst-${key}`, duration: 4000 })
}
