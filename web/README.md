# Beyond Candlesticks - Frontend

React 18 + TypeScript frontend for Transmission™ trading middleware.

## Tech Stack

- **Vite** - Build tool
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **TanStack Query** - Data fetching & caching
- **Zustand** - State management
- **React Router** - Routing
- **Recharts** - Charts (for future P&L visualization)

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env if needed (default: http://localhost:8000)
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Build for production:**
   ```bash
   npm run build
   ```

## Project Structure

```
web/
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── ui/         # shadcn/ui components
│   │   ├── StatusCard.tsx
│   │   ├── KillSwitch.tsx
│   │   ├── OrdersTable.tsx
│   │   └── PositionsTable.tsx
│   ├── pages/          # Page components
│   │   ├── Dashboard.tsx
│   │   └── Trades.tsx
│   ├── lib/            # Utilities & API client
│   │   ├── api.ts      # Axios client
│   │   ├── ws.ts       # WebSocket hook
│   │   ├── types.ts    # TypeScript types
│   │   └── utils.ts    # Helper functions
│   ├── state/          # Zustand stores
│   │   └── uiStore.ts
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
└── package.json
```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000/api` (configurable via `VITE_API_URL`).

### Endpoints Used

- `GET /api/system/status` - System status
- `GET /api/system/orders` - Open orders
- `GET /api/system/positions` - Active positions
- `POST /api/system/flatten_all` - Kill switch
- `GET /api/trades` - Trade history
- `WS /ws` - WebSocket for real-time updates

## WebSocket Events

The frontend subscribes to WebSocket events:
- `regime_change` - Market regime updates
- `signal` - Signal generation
- `order_submitted` - Order placement
- `fill` - Order fills
- `constraint_violation` - Constraint violations
- `guard_reject` - Execution guard rejections
- `flatten_all` - Kill switch activation

## Development

- **Port:** 5173 (Vite default)
- **Hot Reload:** Enabled
- **Type Checking:** TypeScript strict mode
- **Linting:** ESLint configured

## Next Steps

- [ ] Add P&L charts (Recharts)
- [ ] Add metrics visualization
- [ ] Add trade filters
- [ ] Add export functionality
- [ ] Add dark mode toggle
- [ ] Add authentication (future)

