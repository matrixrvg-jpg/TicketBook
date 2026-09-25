import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Ticket, ShieldAlert, Zap, Clock, X } from 'lucide-react';
import { useAuth } from './context/AuthContext';

export default function EventDetails() {
  const { token } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, loading, success, error, in_cart
  const [errorMsg, setErrorMsg] = useState('');
  const [seats, setSeats] = useState([]);
  const [loadingSeats, setLoadingSeats] = useState(true);

  // Cart Timer State
  const [cartTicket, setCartTicket] = useState(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [attendeeName, setAttendeeName] = useState('');
  const [attendeeAge, setAttendeeAge] = useState('');

  const fetchTickets = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/v1/events/${id}/tickets`);
      if (response.data && response.data.data && response.data.data.length > 0) {
        setSeats(response.data.data);
      } else {
        throw new Error("No tickets found for this event in DB.");
      }
    } catch (err) {
      console.warn('Backend not running, falling back to mock seats');
      setSeats(Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        seat_number: `Seat ${i + 1}`,
        status: Math.random() > 0.8 ? 'RESERVED' : 'AVAILABLE',
        version_id: 1,
        section: 'VIP'
      })));
    } finally {
      setLoadingSeats(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [id]);

  useEffect(() => {
    if (cartTicket && cartTicket.expires_at) {
      const interval = setInterval(() => {
        // Python datetime string often looks like: 2026-09-25 15:30:26.123456+00:00
        // JS can parse standard ISO strings. Replace space with T just in case.
        const isoString = cartTicket.expires_at.replace(' ', 'T');
        const expiresTime = new Date(isoString).getTime();
        const now = new Date().getTime();
        const diff = Math.floor((expiresTime - now) / 1000);
        
        if (diff <= 0) {
          setTimeLeft(0);
          clearInterval(interval);
          handleReject(); // Timer expired, release ticket
        } else {
          setTimeLeft(diff);
        }
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [cartTicket]);

  const handleSeatClick = (seat) => {
    if (seat.status !== 'AVAILABLE') return;
    setErrorMsg('');
    setSelectedSeat(seat);
  };

  const handleReserveSpecific = async () => {
    if (!selectedSeat) return;
    if (!token) {
      navigate('/login');
      return;
    }
    setStatus('loading');
    
    try {
      const response = await axios.post('http://localhost:8000/api/v1/checkout/reserve', {
        ticket_id: parseInt(selectedSeat.id)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCartTicket({
        id: response.data.ticket_id,
        expires_at: response.data.expires_at,
        isVIP: true,
        seat_number: selectedSeat.seat_number
      });
      setStatus('in_cart');
    } catch (error) {
      console.error(error);
      if (error.response?.status === 401) {
        navigate('/login');
        return;
      }
      setStatus('error');
      setErrorMsg(error.response?.data?.detail || "High Demand: Someone else grabbed this seat! (Optimistic Concurrency Lock Failed)");
      setSelectedSeat(null);
      fetchTickets(); // Refresh map
    }
  };

  const handleReserveGeneralAdmission = async () => {
    if (!token) {
      navigate('/login');
      return;
    }
    setStatus('loading');
    setSelectedSeat(null);
    try {
      const response = await axios.post('http://localhost:8000/api/v1/checkout/reserve-random', {
        event_id: parseInt(id)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCartTicket({
        id: response.data.ticket_id,
        expires_at: response.data.expires_at,
        isVIP: false,
        seat_number: 'General Admission'
      });
      setStatus('in_cart');
    } catch (error) {
      console.error(error);
      if (error.response?.status === 401) {
        navigate('/login');
        return;
      }
      setStatus('error');
      setErrorMsg(error.response?.data?.detail || "Sold Out: No tickets remain for this event.");
      fetchTickets(); // Refresh map
    }
  };

  const handleConfirmCheckout = async () => {
    setStatus('loading');
    try {
      await axios.post('http://localhost:8000/api/v1/checkout/confirm', {
        ticket_id: parseInt(cartTicket.id),
        attendee_name: cartTicket.isVIP ? attendeeName : null,
        attendee_age: cartTicket.isVIP ? parseInt(attendeeAge) : null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCartTicket(null);
      setStatus('success');
      setTimeout(() => navigate('/'), 3000);
    } catch (error) {
      console.error(error);
      setStatus('error');
      setErrorMsg(error.response?.data?.detail || "Checkout Failed: Timer may have expired.");
      setCartTicket(null);
      fetchTickets();
    }
  };

  const handleReject = () => {
    // Release the cart back to the pool instantly
    setCartTicket(null);
    setStatus('idle');
    setAttendeeName('');
    setAttendeeAge('');
    setSelectedSeat(null);
    fetchTickets();
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="animate-fade-in" style={{ marginTop: '20px', maxWidth: '1000px', margin: '40px auto', padding: '0 24px', position: 'relative' }}>
      
      {/* Modal Overlay for Cart */}
      {status === 'in_cart' && cartTicket && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="glass" style={{ background: 'white', padding: '40px', width: '100%', maxWidth: '500px', borderRadius: '16px', position: 'relative' }}>
            <button onClick={handleReject} style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
              <X size={24} />
            </button>
            
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <h2 style={{ margin: '0 0 8px 0', fontSize: '1.8rem', color: 'var(--primary-blue)' }}>Complete Your Order</h2>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: '#fef3c7', color: '#b45309', padding: '8px 16px', borderRadius: '20px', fontWeight: 600, fontSize: '1.1rem' }}>
                <Clock size={20} />
                {formatTime(timeLeft)}
              </div>
              <p style={{ margin: '16px 0 0 0', color: 'var(--text-muted)' }}>
                We've securely locked <strong>{cartTicket.seat_number}</strong> for you. Please confirm your details before the timer expires.
              </p>
            </div>

            {cartTicket.isVIP && (
              <div style={{ marginBottom: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600 }}>Attendee Name *</label>
                  <input type="text" value={attendeeName} onChange={e => setAttendeeName(e.target.value)} placeholder="Taylor Swift" />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600 }}>Attendee Age *</label>
                  <input type="number" value={attendeeAge} onChange={e => setAttendeeAge(e.target.value)} placeholder="34" />
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                onClick={handleReject}
                style={{ flex: 1, padding: '14px', background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', transition: 'background 0.2s' }}
              >
                Release Ticket
              </button>
              <button 
                onClick={handleConfirmCheckout}
                disabled={cartTicket.isVIP && (!attendeeName || !attendeeAge)}
                className="btn-primary"
                style={{ flex: 2, padding: '14px' }}
              >
                Confirm Purchase
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ marginBottom: '40px', textAlign: 'center' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Select Your Seats</h1>
        <p style={{ color: 'var(--text-muted)' }}>
          Experience our dual-concurrency engine in real-time.
        </p>
      </div>

      <div className="glass" style={{ padding: '40px', background: 'white' }}>
        {status === 'success' ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--primary-blue)' }}>
          <div style={{ fontSize: '4rem', marginBottom: '20px' }}>✓</div>
          <h2>Secured!</h2>
          <p style={{ color: 'var(--text-muted)' }}>Your ticket has been securely locked to your account.</p>
          <p style={{ fontSize: '0.9rem', color: '#64748b', marginTop: '16px' }}>Redirecting to home...</p>
        </div>
      ) : (
        <>
          {/* General Admission Section */}
          <div style={{ background: 'var(--bg-color)', border: '1px solid var(--card-border)', borderRadius: '12px', padding: '32px', marginBottom: '40px', textAlign: 'center' }}>
            <Zap size={32} style={{ color: '#eab308', margin: '0 auto 16px' }} />
            <h3 style={{ margin: '0 0 8px 0', fontSize: '1.5rem' }}>General Admission Fast-Track</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '24px', maxWidth: '500px', margin: '0 auto 24px' }}>
              Don't care where you sit? Click below to let the database find and lock the next available seat using a <strong>Pessimistic SKIP LOCKED</strong> query.
            </p>
            <button 
              className="btn-primary" 
              onClick={handleReserveGeneralAdmission}
              disabled={status === 'loading'}
              style={{ padding: '16px 32px', fontSize: '1.1rem', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            >
              <Ticket size={20} />
              {status === 'loading' ? 'Securing...' : 'Buy Next Available Ticket'}
            </button>
          </div>

          <hr style={{ border: 0, borderTop: '1px solid var(--card-border)', margin: '40px 0' }} />

          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <h3 style={{ margin: '0 0 8px 0' }}>Or, Pick a Specific Seat</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Uses <strong>Optimistic Concurrency Control (OCC)</strong>.
            </p>
          </div>

          <div className="seat-map">
            <div className="stage">STAGE</div>
            {loadingSeats ? (
              <div style={{ padding: '80px', color: 'var(--text-muted)' }}>Loading Live Seat Map...</div>
            ) : (
              <div className="seats-grid">
                {seats.filter(seat => seat.section === 'VIP').map((seat) => (
                  <div
                    key={seat.id}
                    onClick={() => handleSeatClick(seat)}
                    className={`seat ${seat.status.toLowerCase()} ${selectedSeat?.id === seat.id ? 'selected' : ''}`}
                    title={seat.seat_number || `Seat ${seat.id}`}
                  />
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '32px', margin: '40px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
              <div className="seat available" style={{ width: 24, height: 24, cursor: 'default' }} /> Available
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
              <div className="seat selected" style={{ width: 24, height: 24, cursor: 'default' }} /> Selected
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
              <div className="seat reserved" style={{ width: 24, height: 24, cursor: 'default' }} /> Reserved
            </div>
          </div>
          
          {/* Checkout Panel */}
          <div style={{ background: '#f8fafc', border: '1px solid var(--card-border)', borderRadius: '12px', padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.2rem' }}>
                {selectedSeat ? (selectedSeat.seat_number || `Seat #${selectedSeat.id}`) : 'No Seat Selected'}
              </h3>
              <p style={{ margin: '4px 0 0 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                {selectedSeat ? 'VIP Specific Admission' : 'Click a blue seat on the map above'}
              </p>
            </div>
            
            <button 
              className="btn-primary" 
              onClick={handleReserveSpecific}
              disabled={!selectedSeat || status === 'loading'}
              style={{ display: 'flex', gap: '8px', alignItems: 'center', padding: '16px 32px' }}
            >
              <Ticket size={20} />
              Checkout Specific Seat
            </button>
          </div>

          {status === 'error' && (
            <div style={{ marginTop: '24px', padding: '16px', background: '#fef2f2', color: '#991b1b', borderRadius: '8px', border: '1px solid #fecaca', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
              <ShieldAlert size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ display: 'block', marginBottom: '4px' }}>Checkout Failed</strong>
                {errorMsg}
              </div>
            </div>
          )}
        </>
      )}
      </div>
    </div>
  );
}
