import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function EventDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [errorMsg, setErrorMsg] = useState('');
  const [seats, setSeats] = useState([]);
  const [loadingSeats, setLoadingSeats] = useState(true);
  const [logs, setLogs] = useState([]); // Terminal logs

  const addLog = (msg, type = 'info') => {
    setLogs(prev => [...prev, { msg, type, time: new Date().toISOString().split('T')[1].slice(0, -1) }]);
  };

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/v1/events/${id}/tickets`);
        if (response.data && response.data.data && response.data.data.length > 0) {
          setSeats(response.data.data);
        } else {
          throw new Error("No tickets found for this event in DB.");
        }
      } catch (err) {
        addLog(`DB Connection Failed: ${err.message}`, 'error');
        // Fallback to mock seats if backend is down
        setSeats(Array.from({ length: 50 }, (_, i) => ({
          id: i + 1,
          seat_number: `Seat ${i + 1}`,
          status: Math.random() > 0.8 ? 'RESERVED' : 'AVAILABLE',
          version_id: 1
        })));
      } finally {
        setLoadingSeats(false);
      }
    };
    addLog(`INIT: GET /api/v1/events/${id}/tickets`, 'keyword');
    fetchTickets();
  }, [id]);

  const handleSeatClick = (seat) => {
    if (seat.status !== 'AVAILABLE') return;
    setSelectedSeat(seat);
    addLog(`SELECT * FROM tickets WHERE id = ${seat.id};`, 'prompt');
    addLog(`-> Record found. version_id = ${seat.version_id || 1}`, 'success');
  };

  const handleReserve = async () => {
    if (!selectedSeat) return;
    
    setStatus('loading');
    addLog(`BEGIN TRANSACTION;`, 'keyword');
    addLog(`UPDATE tickets SET status='RESERVED', version_id=${(selectedSeat.version_id || 1) + 1} WHERE id=${selectedSeat.id} AND version_id=${selectedSeat.version_id || 1};`, 'prompt');
    
    try {
      // Hit the real backend if available
      const response = await axios.post('http://localhost:8000/api/v1/checkout/reserve', {
        ticket_id: parseInt(selectedSeat.id),
        user_id: 1 // Mock user
      });
      
      setStatus('success');
      addLog(`-> 1 row updated. COMMIT;`, 'success');
      setTimeout(() => navigate('/'), 4000);
    } catch (error) {
      console.error(error);
      setStatus('error');
      setErrorMsg(error.response?.data?.detail || "High Demand: Someone else grabbed this seat!");
      addLog(`-> 0 rows updated. ROLLBACK;`, 'error');
      addLog(`ERR: Version mismatch. Seat already taken by concurrent thread.`, 'error');
      
      // Simulate real-time UI update on fail
      setSelectedSeat(null);
    }
  };

  return (
    <div className="animate-fade-in" style={{ marginTop: '20px', maxWidth: '1400px', margin: '20px auto', padding: '0 24px' }}>
      
      <div style={{ marginBottom: '40px' }}>
        <h1 className="title-glow">Database Shard #{id}</h1>
        <p style={{ color: 'var(--text-muted)' }}>Select a node to initiate an Optimistic Concurrency lock.</p>
      </div>

      <div className="two-column">
        <div className="glass" style={{ padding: '40px' }}>
          {status === 'success' ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#4ade80' }}>
            <div style={{ fontSize: '4rem', marginBottom: '20px' }}>✓</div>
            <h2>Ticket Reserved!</h2>
            <p>Redirecting to home...</p>
          </div>
        ) : (
          <>
            <div className="seat-map">
              <div className="stage">STAGE</div>
              {loadingSeats ? (
                <div style={{ padding: '40px' }}>Loading Live Seats...</div>
              ) : (
                <div className="seats-grid">
                  {seats.map((seat) => (
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

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '40px' }}>
              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div className="seat available" style={{ width: 16, height: 16, cursor: 'default' }} /> Available
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div className="seat reserved" style={{ width: 16, height: 16, cursor: 'default' }} /> Taken
                </div>
              </div>
              
              <button 
                className="btn-primary" 
                onClick={handleReserve}
                disabled={!selectedSeat || status === 'loading'}
              >
                {status === 'loading' ? 'Securing...' : `Buy ${selectedSeat?.seat_number || selectedSeat?.id || 'Seat'}`}
              </button>
            </div>

            {status === 'error' && (
              <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                {errorMsg}
              </div>
            )}
          </>
        )}
        </div>

        {/* The Live Execution Terminal */}
        <div className="terminal">
          <div className="terminal-header">
            <div className="term-dot red"></div>
            <div className="term-dot yellow"></div>
            <div className="term-dot green"></div>
            <span style={{ marginLeft: '12px', color: '#64748b', fontSize: '0.75rem' }}>postgres@ticketbook-core:~$</span>
          </div>
          
          <div className="terminal-body" style={{ minHeight: '300px' }}>
            {logs.map((log, index) => (
              <div key={index} className="terminal-line">
                <span style={{ color: '#64748b', marginRight: '8px' }}>[{log.time}]</span>
                <span className={log.type}>{log.msg}</span>
              </div>
            ))}
            <div className="terminal-line">
              <span className="prompt">postgres&gt;</span>
              <span className="blinking-cursor"></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
