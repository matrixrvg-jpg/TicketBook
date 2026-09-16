import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Ticket, Shield } from 'lucide-react';
import Home from './Home';
import EventDetails from './EventDetails';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import { AuthProvider, useAuth } from './context/AuthContext';

function Navigation() {
  const { token } = useAuth();
  return (
    <nav>
      <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
        <Link to="/" className="nav-brand">
          <Ticket size={28} />
          <span>Ticketbook</span>
        </Link>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          {token ? (
            <Link to="/dashboard" className="btn-outline" style={{ display: 'flex', gap: '8px', alignItems: 'center', padding: '8px 16px' }}>
              <Shield size={18} /> Dashboard
            </Link>
          ) : (
            <Link to="/login" className="btn-primary" style={{ padding: '8px 16px', fontSize: '0.9rem' }}>
              Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="app">
          <Navigation />
          
          <main className="container" style={{ minHeight: 'calc(100vh - 72px)', paddingBottom: '40px' }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/event/:id" element={<EventDetails />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
