import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';
import { createSession } from './auth';
import GuestPage from './GuestPage';
import {sharingEnabled} from './sharing';

const guest=sharingEnabled&&location.pathname==='/guest';
const session = guest?null:createSession();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {guest?<GuestPage/>:<App session={session!}/>}
  </React.StrictMode>
);
