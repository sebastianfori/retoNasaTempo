import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

const RequireAuth = ({ children }) => {
  const { user, loading } = useAuth();
  const loc = useLocation();

  if (loading) return <div style={{ padding: 24 }}>Cargando sesión…</div>;
  if (!user) return <Navigate to="/login" state={{ from: loc }} replace />;

  return <>{children}</>;
};

export default RequireAuth;
