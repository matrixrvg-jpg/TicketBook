import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, LogOut, Plus, Building } from 'lucide-react';
import axios from 'axios';

export default function Dashboard() {
  const { token, user, tenantId, isTenantLoading, setTenantId, logout } = useAuth();
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  
  // Tenant Form
  const [businessName, setBusinessName] = useState('');
  const [businessEmail, setBusinessEmail] = useState('');
  const [tenantError, setTenantError] = useState('');

  // Event Form
  const [showEventModal, setShowEventModal] = useState(false);
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [capacity, setCapacity] = useState(100);
  const [eventError, setEventError] = useState('');

  useEffect(() => {
    if (tenantId) {
      axios.get('http://localhost:8000/api/v1/events/dashboard')
        .then(res => setEvents(res.data.data))
        .catch(err => console.error(err));
    }
  }, [tenantId]);

  if (!token) {
    return (
      <div className="animate-fade-in glass" style={{ padding: '60px', textAlign: 'center', marginTop: '40px' }}>
        <ShieldAlert size={48} style={{ color: '#ef4444', margin: '0 auto 20px' }} />
        <h2 style={{ marginBottom: '16px' }}>Access Denied</h2>
        <button onClick={() => navigate('/login')} className="btn-primary">Go to Login</button>
      </div>
    );
  }

  if (isTenantLoading) {
    return <div style={{ textAlign: 'center', marginTop: '100px' }}>Loading Command Center...</div>;
  }

  const handleCreateTenant = async (e) => {
    e.preventDefault();
    setTenantError('');
    try {
      const res = await axios.post('http://localhost:8000/api/v1/tenants/', {
        name: businessName,
        business_email: businessEmail
      });
      setTenantId(res.data.id);
    } catch (err) {
      setTenantError(err.response?.data?.detail || 'Failed to create business profile');
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    setEventError('');
    try {
      await axios.post('http://localhost:8000/api/v1/events/', {
        title,
        date: new Date(date).toISOString(),
        max_capacity: parseInt(capacity)
      });
      setShowEventModal(false);
      // Refresh events
      const res = await axios.get('http://localhost:8000/api/v1/events/dashboard');
      setEvents(res.data.data);
    } catch (err) {
      setEventError(err.response?.data?.detail || 'Failed to create event');
    }
  };

  if (!tenantId) {
    return (
      <div className="animate-fade-in" style={{ display: 'flex', justifyContent: 'center', marginTop: '60px' }}>
        <div className="glass" style={{ padding: '40px', width: '100%', maxWidth: '400px', background: 'white' }}>
          <Building size={48} style={{ color: 'var(--primary-blue)', margin: '0 auto 20px' }} />
          <h2 style={{ marginBottom: '16px', textAlign: 'center' }}>Business Profile Required</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', textAlign: 'center', fontSize: '0.9rem' }}>
            You must register your Organizer entity before you can initialize events.
          </p>
          {tenantError && <div style={{ color: '#ef4444', marginBottom: '16px' }}>{tenantError}</div>}
          <form onSubmit={handleCreateTenant} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)', fontWeight: 600 }}>Business Name</label>
              <input type="text" required value={businessName} onChange={e => setBusinessName(e.target.value)} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)', fontWeight: 600 }}>Support Email</label>
              <input type="email" required value={businessEmail} onChange={e => setBusinessEmail(e.target.value)} />
            </div>
            <button type="submit" className="btn-primary" style={{ marginTop: '16px' }}>Register Business</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ marginTop: '40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
        <div>
          <span className="tech-badge" style={{ marginBottom: '12px', display: 'inline-block' }}>
            Tenant ID: {tenantId} | Role: {user?.role}
          </span>
          <h2>Organizer Dashboard</h2>
          <p style={{ color: 'var(--text-muted)' }}>Manage your high-concurrency event shards.</p>
        </div>
        <button onClick={() => { logout(); navigate('/'); }} className="btn-primary" style={{ background: 'transparent', border: '1px solid var(--card-border)', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <LogOut size={16} /> Terminate Session
        </button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h3>Active Event Shards</h3>
        <button onClick={() => setShowEventModal(true)} className="btn-primary" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Plus size={18} /> Initialize Event
        </button>
      </div>

      {events.length === 0 ? (
        <div className="glass" style={{ padding: '40px', textAlign: 'center', borderStyle: 'dashed' }}>
          <p style={{ color: 'var(--text-muted)' }}>No Active Shards. Initialize a new event cluster to begin selling tickets.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
          {events.map(ev => (
            <div key={ev.id} className="event-card" style={{ cursor: 'default' }}>
              <h4 style={{ marginBottom: '8px', color: 'var(--text-main)' }}>{ev.title}</h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '16px' }}>
                {new Date(ev.date).toLocaleDateString()}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--card-border)', paddingTop: '16px' }}>
                <span style={{ fontSize: '0.9rem' }}>Capacity</span>
                <span className="tech-badge">{ev.sold_tickets || 0} / {ev.max_capacity}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Event Modal */}
      {showEventModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="glass animate-fade-in" style={{ padding: '32px', width: '100%', maxWidth: '400px', background: 'white' }}>
            <h3 style={{ marginBottom: '24px' }}>Create New Event</h3>
            {eventError && <div style={{ color: '#ef4444', marginBottom: '16px' }}>{eventError}</div>}
            <form onSubmit={handleCreateEvent} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)', fontWeight: 600 }}>Event Title</label>
                <input type="text" required value={title} onChange={e => setTitle(e.target.value)} />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)', fontWeight: 600 }}>Date & Time</label>
                <input type="datetime-local" required value={date} onChange={e => setDate(e.target.value)} />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)', fontWeight: 600 }}>Ticket Capacity</label>
                <input type="number" required min="1" max="5000" value={capacity} onChange={e => setCapacity(e.target.value)} />
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                <button type="button" onClick={() => setShowEventModal(false)} className="btn-outline" style={{ flex: 1 }}>Cancel</button>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
