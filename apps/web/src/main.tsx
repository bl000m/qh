import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';
import { createSession } from './auth';

const session = createSession();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App session={session} />
  </React.StrictMode>
);
