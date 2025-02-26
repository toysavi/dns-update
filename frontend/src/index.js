import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';  // Add this if you have any CSS
import App from './App';  // Import the App component

// Rendering the App component inside the root div in your public/index.html
ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);
