import React from 'react'
import { SessionProvider } from './context/SessionContext'
import Navbar    from './components/Navbar'
import Footer    from './components/Footer'
import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <SessionProvider>
      <div className="app-layout">
        <Navbar />
        <div className="app-body">
          <Dashboard />
        </div>
        <Footer />
      </div>
    </SessionProvider>
  )
}
