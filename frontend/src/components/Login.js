import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../AuthContext';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();
    const { setUser } = useAuth(); // Destructure login from useAuth

    const handleSubmit = async (event) => {
        event.preventDefault(); // Prevent default form submission behavior
        try {
            const response = await axios.post('https://dry-dawn-86507-cc866b3e1665.herokuapp.com/auth/login', { username, password }, {
                withCredentials: true
            });
            if (response.status === 200) {
                setUser({ username });  // Update the user state to reflect login
                navigate(`/profile`);  // Navigate to the user's profile page
            } else {
                console.error('Login failed:', response.data.message);
            }
        } catch (error) {
            console.error('Login failed:', error.response ? error.response.data.message : 'Server Error');
        }
    };

    return (
        <div>
            <header>
                <h1>Login to Your Account</h1>
            </header>
            <div id="main-content">
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="username">Username:</label>
                        <input type="text" id="username" name="username" required onChange={(e) => setUsername(e.target.value)} autoComplete="off" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">Password:</label>
                        <input type="password" id="password" name="password" required onChange={(e) => setPassword(e.target.value)} autoComplete="off" />
                    </div>
                    <button type="submit" className="button">Login</button>
                </form>
                <p>Don't have an account? <a href="/register">Create one now</a>.</p>
                <a href="/" className="button">Back to Homepage</a>
            </div>
        </div>
    );
}

export default Login;