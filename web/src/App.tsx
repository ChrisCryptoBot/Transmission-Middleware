import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import Trades from './pages/Trades';
import { useUIStore } from './state/uiStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);
  const setSidebarOpen = useUIStore((state) => state.setSidebarOpen);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-background">
          {/* Navigation */}
          <nav className="border-b">
            <div className="container mx-auto px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                  <Link to="/" className="text-xl font-bold">
                    Beyond Candlesticks
                  </Link>
                  <div className="flex gap-4">
                    <Link
                      to="/"
                      className="text-sm font-medium text-muted-foreground hover:text-foreground"
                    >
                      Dashboard
                    </Link>
                    <Link
                      to="/trades"
                      className="text-sm font-medium text-muted-foreground hover:text-foreground"
                    >
                      Trades
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/trades" element={<Trades />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

