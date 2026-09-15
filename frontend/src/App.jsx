import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Ticket } from 'lucide-react';
import Home from './Home';
import EventDetails from './EventDetails';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="glass-panel">
          <div className="container">
            <Link to="/" className="nav-brand">
              <Ticket className="text-indigo-400" size={28} />
              <span>Ticketbook</span>
            </Link>
          </div>
        </nav>
        
        <main className="container" style={{ minHeight: 'calc(100vh - 72px)', paddingBottom: '40px' }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/event/:id" element={<EventDetails />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
