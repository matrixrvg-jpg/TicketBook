import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Calendar, Users, MapPin, ChevronRight, Activity } from 'lucide-react';

export default function Home() {
  const [events, setEvents] = useState([]);
  
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/v1/events/public');
        if (response.data && response.data.data.length > 0) {
          setEvents(response.data.data);
        }
      } catch (error) {
        console.warn('Backend error', error);
      }
    };
    fetchEvents();
  }, []);

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <section className="hero-banner" style={{ marginTop: '24px' }}>
        <div className="hero-content">
          <h1>Discover Live Events</h1>
          <p>
            Powered by our ultra-fast Concurrency Engine. Guaranteeing your tickets, even under massive scale.
          </p>
          <div style={{ marginTop: '32px', display: 'flex', gap: '16px' }}>
            <span className="tech-badge" style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid rgba(255,255,255,0.2)' }}>
              <Activity size={14} style={{ display: 'inline', marginRight: '4px' }} />
              PostgreSQL CTE Bulk Insertion
            </span>
            <span className="tech-badge" style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid rgba(255,255,255,0.2)' }}>
              Optimistic Concurrency Control
            </span>
          </div>
        </div>
      </section>

      {/* Events List */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2>Trending Near You</h2>
          <span style={{ color: 'var(--primary-blue)', fontWeight: 600, fontSize: '0.9rem' }}>
            {events.length} Events Available
          </span>
        </div>

        {events.length === 0 ? (
          <div className="glass" style={{ padding: '60px', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-muted)' }}>No events are currently scheduled.</p>
          </div>
        ) : (
          <div className="events-grid">
            {events.map((event) => {
              const dateObj = new Date(event.date);
              const dayOfWeek = dateObj.toLocaleDateString('en-US', { weekday: 'short' });
              const month = dateObj.toLocaleDateString('en-US', { month: 'short' });
              const day = dateObj.toLocaleDateString('en-US', { day: 'numeric' });
              const time = dateObj.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

              return (
                <Link to={`/event/${event.id}`} key={event.id} className="event-card">
                  <div style={{ display: 'flex', gap: '16px' }}>
                    
                    {/* Date Block */}
                    <div style={{ textAlign: 'center', minWidth: '60px' }}>
                      <div style={{ color: 'var(--primary-blue)', fontSize: '0.9rem', fontWeight: 600, textTransform: 'uppercase' }}>{month}</div>
                      <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: '1' }}>{day}</div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '4px' }}>{dayOfWeek}</div>
                    </div>
                    
                    {/* Event Details */}
                    <div style={{ flex: 1 }}>
                      <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem' }}>{event.title}</h3>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Calendar size={14} /> {time}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <MapPin size={14} /> {event.venue || `Global Server Shard #${event.tenant_id}`}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Users size={14} /> {event.max_capacity} Max Capacity
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Action Button */}
                  <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--card-border)', display: 'flex', justifyContent: 'flex-end' }}>
                    <span className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '8px 16px', fontSize: '0.9rem' }}>
                      See Tickets <ChevronRight size={16} />
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
