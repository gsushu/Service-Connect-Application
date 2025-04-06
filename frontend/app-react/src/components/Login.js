import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

import "../styles/Login.css";

function Login() {
  const [userName, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginSuccessful, setLoginSuccessful] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    setUsername("");
    setPassword("");
    setMessage("");
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const login_data = {
        username: userName,
        password: password,
      };
      const response = await axios.post(
        "http://localhost:8000/login",
        login_data,
        { withCredentials: true }
      );
      setLoginSuccessful(true);
      setMessage(response.data.message);
      navigate("/home", { state: { username: userName } });
    } catch (error) {
      if (error.response) {
        setLoginSuccessful(false);
        setMessage(
          `Login failed: ${error.response.data.detail || "Unknown error"}`
        );
      } else {
        setLoginSuccessful(false);
        setMessage(`Error: ${error.message}`);
      }
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <div>
          <label>Username:</label>
          <input
            type="text"
            value={userName}
            onChange={(e) => setUsername(e.target.value)}
            required
          />

          <label>Password:</label>
          <input
            type="text"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">Login</button>
      </form>
      {message && (
        <p style={{ color: loginSuccessful ? "green" : "red" }}>{message}</p>
      )}
    </div>
  );
}

export default Login;
