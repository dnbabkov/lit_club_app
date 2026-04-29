import React from 'react'
import ReactDOM from 'react-dom/client'
import { Providers } from "./app/providers.tsx";
import './index.css'
import App from './App.tsx'

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <Providers>
            <App />
        </Providers>
    </React.StrictMode>
)
