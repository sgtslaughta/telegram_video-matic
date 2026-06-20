import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { Toaster } from 'sonner'

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
      <BrowserRouter>
        <div className="h-screen bg-white dark:bg-black">
          <h1 className="text-2xl font-bold p-4">Video-Matic</h1>
          <p className="p-4">Frontend scaffold ready.</p>
        </div>
        <Toaster position="bottom-right" />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
