import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { setExtraHeaders } from '@workspace/api-client-react';

function getDeviceId(): string {
  let id = localStorage.getItem('tre_device_id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('tre_device_id', id);
  }
  return id;
}

setExtraHeaders({ 'X-Device-Id': getDeviceId() });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
