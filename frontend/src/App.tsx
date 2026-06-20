import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { ThemeProvider } from '@/hooks/useTheme'
import { AccentProvider } from '@/hooks/useAccent'
import { TooltipProvider } from '@/components/ui/tooltip'
import Router from '@/Router'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 min
      gcTime: 1000 * 60 * 10,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AccentProvider>
        <TooltipProvider>
          <BrowserRouter>
            <Router />
            <Toaster position="bottom-right" />
          </BrowserRouter>
        </TooltipProvider>
        </AccentProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
