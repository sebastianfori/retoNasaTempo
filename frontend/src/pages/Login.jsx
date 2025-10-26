import React from "react";

const Login = () => {
  const loginUrl = `${import.meta.env.VITE_BACKEND_URL}/auth/google/login`;
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#f8fafc" }}>
      <div className="p-8 rounded-2xl shadow bg-white w-full max-w-md text-center">
        <h1 className="text-2xl" style={{ fontWeight: 600, marginBottom: 12 }}>Ingresá</h1>
        <p style={{ color: "#475569", marginBottom: 16 }}>Usá tu cuenta de Google para continuar.</p>
        <a
          href={loginUrl}
          style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "100%", border: "1px solid #e2e8f0", borderRadius: 8, padding: "12px 16px" }}
        >
          <img alt="Google" src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" style={{ width: 20, height: 20, marginRight: 12 }} />
          Continuar con Google
        </a>
      </div>
    </div>
  );
};

export default Login;
