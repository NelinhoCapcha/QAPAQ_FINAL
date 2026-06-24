import { BadgeCheck, BarChart3, Building2, DatabaseZap, FileSearch, Landmark, ShieldCheck, UsersRound } from 'lucide-react'
import { Navigate } from 'react-router-dom'
import LoginForm from '../components/forms/LoginForm.jsx'
import Logo from '../components/ui/Logo.jsx'
import { useAuth } from '../hooks/useAuth.js'

export default function HomePage() {
  const { isAuthenticated, loading, error, iniciarSesion } = useAuth()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="qapaq-home">
      <header className="qapaq-home__bar">
        <Logo size={78} />
        <span className="qapaq-secure">
          <ShieldCheck size={15} strokeWidth={2.4} />
          Conexion segura
        </span>
      </header>

      <main className="qapaq-home__main">
        <section className="qapaq-home__login" aria-labelledby="home-login-title">
          <span className="qapaq-pill">
            <ShieldCheck size={15} strokeWidth={2.4} />
            Acceso interno Core Bancario
          </span>
          <h1 id="home-login-title">Mesa operativa del Core Financiero</h1>
          <p>Gestiona clientes, cartera, solicitudes y seguimiento comercial desde el entorno interno del banco.</p>

          <div className="qapaq-login-card">
            <div className="qapaq-login-card__head">
              <div>
                <span>Core Bancario QAPAQ</span>
                <h2>Acceso del personal</h2>
              </div>
              <span className="qapaq-lock">
                <ShieldCheck size={22} strokeWidth={2.2} />
              </span>
            </div>
            <LoginForm onSubmit={iniciarSesion} loading={loading} error={error} />
          </div>
        </section>

        <section className="qapaq-core-panel" aria-label="Funciones del Core Bancario QAPAQ">
          <div className="qapaq-core-panel__header">
            <span>CORE FINANCIERO</span>
            <strong>Que puedes operar</strong>
          </div>

          <div className="qapaq-core-panel__grid">
            <div className="qapaq-core-metric qapaq-core-metric--primary">
              <UsersRound size={22} />
              <span>Clientes</span>
              <strong>Registro y consulta</strong>
            </div>
            <div className="qapaq-core-metric">
              <Landmark size={22} />
              <span>Cartera</span>
              <strong>Creditos y saldos</strong>
            </div>
            <div className="qapaq-core-metric">
              <DatabaseZap size={22} />
              <span>Solicitudes</span>
              <strong>Flujo crediticio</strong>
            </div>
            <div className="qapaq-core-metric">
              <BadgeCheck size={22} />
              <span>Scoring</span>
              <strong>Riesgo y decision</strong>
            </div>
            <div className="qapaq-core-metric">
              <BarChart3 size={22} />
              <span>Dashboard</span>
              <strong>Indicadores clave</strong>
            </div>
            <div className="qapaq-core-metric">
              <FileSearch size={22} />
              <span>Recuperaciones</span>
              <strong>Seguimiento y mora</strong>
            </div>
          </div>

          <div className="qapaq-core-workflow">
            <div>
              <Building2 size={18} />
              <span>Agencia</span>
              <strong>Huancayo Centro</strong>
            </div>
            <div>
              <span>Modulo</span>
              <strong>Creditos y riesgo</strong>
            </div>
            <div>
              <span>Estado</span>
              <strong>Disponible</strong>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
