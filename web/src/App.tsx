/**
 * VEGUS App - Main Application Component
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/transmission" element={<Dashboard />} />
          <Route path="/strategies" element={<Dashboard />} />
          <Route path="/analytics" element={<Dashboard />} />
          <Route path="/risk" element={<Dashboard />} />
          <Route path="/execution" element={<Dashboard />} />
          <Route path="/system" element={<Dashboard />} />
          <Route path="/settings" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

