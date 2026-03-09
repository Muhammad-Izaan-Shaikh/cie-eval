import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 1000 * 60,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a1208',
            color: '#f5f0e8',
            fontFamily: '"Source Serif 4", serif',
            fontSize: '14px',
            borderRadius: '0',
          },
          success: {
            iconTheme: { primary: '#4a6741', secondary: '#f5f0e8' },
          },
          error: {
            iconTheme: { primary: '#8b1a1a', secondary: '#f5f0e8' },
          },
        }}
      />
    </QueryClientProvider>
  </React.StrictMode>
)
