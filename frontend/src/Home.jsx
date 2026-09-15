import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Calendar, Users } from 'lucide-react';

const MOCK_EVENTS = [
  { id: 1, title: "Cyberpunk 2077 Symphony", date: "2026-10-15T19:00:00Z", max_capacity: 100 },
  { id: 2, title: "AI Developers Conference", date: "2026-11-20T09:00:00Z", max_capacity: 500 },
  { id: 3, title: "Midnight Synthwave Fest", date: "2026-12-05T22:00:00Z", max_capacity: 200 }
];

export default function Home() {
  const [events, setEvents] = useState(MOCK_EVENTS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Attempt to fetch from real backend, fallback to mock if it fails
    const fetchEvents = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/v1/events');
        if (response.data && response.data.data.length > 0) {
          setEvents(response.data.data);
        }
      } catch (error) {
        console.warn('Backend not running or empty, using mock events for UI demonstration.');
      }
    };
    fetchEvents();
  }, []);

  return (
    <div className="animate-fade-in" style={{ marginTop: '20px' }}>
      <div style={{ padding: '60px 0', borderBottom: '1px solid var(--card-border)', marginBottom: '40px' }}>
        <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
          <span className="tech-badge">PostgreSQL CTE</span>
          <span className="tech-badge">Optimistic Concurrency</span>
          <span className="tech-badge">Multi-Tenant</span>
        </div>
        <h1 className="title-glow" style={{ fontSize: '3.5rem', marginBottom: '16px' }}>
          High-Concurrency Core
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.2rem', maxWidth: '600px', lineHeight: '1.6' }}>
          A demonstration of enterprise backend scalability. Handling massive race conditions via row-level locking and versioning without degrading performance.
        </p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', margin: 0 }}>Active Database Shards</h2>
        <span style={{ color: 'var(--accent)', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.9rem' }}>
          Status: Online
        </span>
      </div>

      <div className="events-grid">
        {events.map((event) => (
          <Link to={`/event/${event.id}`} key={event.id} className="event-card glass">
            <div className="card-header">
              <span className="date-badge">
                {new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
            </div>
            <h2 className="event-title">{event.title}</h2>
            <div style={{ display: 'flex', gap: '16px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Calendar size={16} />
                {new Date(event.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Users size={16} />
                {event.max_capacity} Cap
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
