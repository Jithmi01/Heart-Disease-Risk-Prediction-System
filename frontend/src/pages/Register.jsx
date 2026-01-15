import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Register({ switchPage }) {
  const { register } = useAuth();
  const { theme } = useTheme();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async e => {
    e.preventDefault();
    setError("");
    try {
      await register(name, email, password);
      setSuccess(true);
      setTimeout(() => switchPage(), 2000);
    } catch (err) {
      setError(err.response?.data?.error || "Registration failed");
    }
  };

  return (
    <div className={`min-h-screen flex justify-center items-center ${
      theme === "dark" ? "bg-gray-900" : "bg-blue-50"
    }`}>
      <div className={`p-8 rounded-xl shadow-lg w-full max-w-md ${
        theme === "dark" ? "bg-gray-800 text-white" : "bg-white text-gray-900"
      }`}>
        <h1 className="text-2xl font-bold mb-4 text-center">Register</h1>
        {error && <div className="text-red-600 mb-2">{error}</div>}
        {success && <div className="text-green-600 mb-2">Registered successfully!</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="text" placeholder="Full Name" value={name}
            onChange={e => setName(e.target.value)}
            className="w-full p-2 rounded border" required/>
          <input type="email" placeholder="Email" value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full p-2 rounded border" required/>
          <input type="password" placeholder="Password" value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full p-2 rounded border" required/>
          <button className="w-full p-2 bg-blue-600 rounded text-white">Register</button>
        </form>
        <p className="mt-4 text-center">
          Already have an account?
          <button className="text-blue-500 ml-1" onClick={switchPage}>Login</button>
        </p>
      </div>
    </div>
  );
}
