import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null); 
  const [tenantId, setTenantId] = useState(null);
  const [isTenantLoading, setIsTenantLoading] = useState(true);

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUser(payload);
        
        // Fetch tenant ID
        axios.get('http://localhost:8000/api/v1/tenants/my')
          .then(res => {
            setTenantId(res.data.tenant_id);
            setIsTenantLoading(false);
          })
          .catch(() => {
            setTenantId(null);
            setIsTenantLoading(false);
          });
      } catch(e) {
        console.error("Invalid token format");
        setIsTenantLoading(false);
      }
    } else {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
      setTenantId(null);
      setIsTenantLoading(false);
    }
  }, [token]);

  const login = (newToken) => {
    setToken(newToken);
  };

  const logout = () => {
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, tenantId, isTenantLoading, setTenantId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
