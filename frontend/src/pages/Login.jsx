import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Login({ switchPage }) {
  const { login } = useAuth();
  const { theme } = useTheme();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async e => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.error || "Login failed");
    }
  };

  return (
    <div className={`min-h-screen flex justify-center items-center ${
      theme === "dark" ? "bg-gray-900" : "bg-blue-50"
    }`}>
      <div className={`p-8 rounded-xl shadow-lg w-full max-w-md ${
        theme === "dark" ? "bg-gray-800 text-white" : "bg-white text-gray-900"
      }`}>
        <h1 className="text-2xl font-bold mb-4 text-center">Login</h1>
        {error && <div className="text-red-600 mb-2">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="email" placeholder="Email" value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full p-2 rounded border" required/>
          <input type="password" placeholder="Password" value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full p-2 rounded border" required/>
          <button className="w-full p-2 bg-blue-600 rounded text-white">Login</button>
        </form>
        <p className="mt-4 text-center">
          Don't have an account? 
          <button className="text-blue-500 ml-1" onClick={switchPage}>Register</button>
        </p>
      </div>
    </div>
  );
}
