import React from "react";
import Retonasa from "../assets/retonasa.png"; 

const Login = () => {
  const loginUrl = `${import.meta.env.VITE_BACKEND_URL}/auth/google/login`;

  
  const page = {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    background: "#0f1116",
    color: "#e5e7eb",
    padding: "24px",
    position: "relative",
  };

  const card = {
    width: "100%",
    maxWidth: "420px",
    background: "#1a1d24",
    border: "1px solid #2a2f3a",
    borderRadius: "16px",
    boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
    padding: "32px",
    textAlign: "center",
  };

  const title = {
    fontSize: "28px",
    fontWeight: 700,
    margin: 0,
    marginBottom: "8px",
    color: "#f3f4f6",
  };

  const subtitle = {
    color: "#9aa3b2",
    margin: 0,
    marginBottom: "24px",
    fontSize: "15px",
  };

  const btn = {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "12px",
    width: "100%",
    padding: "12px 16px",
    borderRadius: "10px",
    background: "#ffffff",
    color: "#111827",
    fontWeight: 600,
    textDecoration: "none",
    border: "1px solid #e5e7eb",
    transition: "background .15s ease, transform .05s ease",
  };

  const googleIcon = { width: "20px", height: "20px", flexShrink: 0 };
  const footer = {
    marginTop: "24px",
    color: "#6b7280",
    fontSize: "12px",
  };

  return (
    <div style={page}>
      {/* 🌌 Imagen giratoria */}
      <img src={Retonasa} alt="NASA Logo" className="rotating-badge" />

      <div style={card}>
        <h1 style={title}>Ingresa</h1>
        <p style={subtitle}>Usa tu cuenta de Google para continuar.</p>

        <a href={loginUrl} style={btn}>
          <img
            alt="Google"
            src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
            style={googleIcon}
          />
          Continuar con Google
        </a>
      </div>

      <p style={footer}>
        © {new Date().getFullYear()} AireClaro • NASA Challenge
      </p>
    </div>
  );
};

export default Login;
