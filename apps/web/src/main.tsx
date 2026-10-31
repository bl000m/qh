import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';
import { createSession, completeSilentCallback } from './auth';
import GuestPage from './GuestPage';
import {sharingEnabled} from './sharing';

if (window.self !== window.top && location.pathname === '/oidc/callback') {
  // The parent OIDC client validates the response; no application mounts in its iframe.
  void completeSilentCallback().catch(() => {/* The parent handles an invalid or timed-out restoration. */});
} else {
  const guest=sharingEnabled&&location.pathname==='/guest';
  const session = guest?null:createSession();

  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      {guest?<GuestPage/>:<App session={session!}/>}
    </React.StrictMode>
  );
}
