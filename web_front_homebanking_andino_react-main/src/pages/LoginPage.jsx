import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  CreditCard,
  Fingerprint,
  Lock,
  ShieldCheck,
  UserRound,
} from 'lucide-react'
import { useHBAuth } from '../hooks/useHBAuth.js'
import { extractError } from '../utils/format.js'
import Logo from '../components/ui/Logo.jsx'
import portadaLogin from '../assets/images/Portada_Login-BFncWR9n.png'

export default function LoginPage() {
  const { login, isAuthenticated } = useHBAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [tarjeta, setTarjeta] = useState(location.state?.tarjeta || '')
  const [dni, setDni] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [recordar, setRecordar] = useState(true)

  useEffect(() => {
    if (isAuthenticated) navigate('/inicio', { replace: true })
  }, [isAuthenticated, navigate])

  const onSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!/^\d{8}$/.test(dni.trim())) {
      setError('Ingresa un DNI valido de 8 digitos.')
      return
    }

    setLoading(true)
    try {
      await login(tarjeta.trim(), dni.trim(), password)
      navigate('/inicio', { replace: true })
    } catch (err) {
      setError(extractError(err, 'No se pudo iniciar sesion.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="qapaq-login">
      <header className="qapaq-login__topbar">
        <Logo size={78} />
        <span className="qapaq-secure">
          <ShieldCheck size={15} strokeWidth={2.4} />
          Conexion segura
        </span>
      </header>

      <main className="qapaq-login__content">
        <section className="qapaq-login__access" aria-labelledby="login-title">
          <span className="qapaq-pill">
            <ShieldCheck size={15} strokeWidth={2.4} />
            Acceso seguro Home Banking
          </span>
          <h1 id="login-title">Ingresa a tu banca electronica</h1>
          <p>Consulta tus productos, realiza operaciones y gestiona tus pagos desde un entorno confiable.</p>

          <div className="qapaq-login-card">
            <div className="qapaq-login-card__head">
              <div>
                <span>QAPAQ en linea</span>
                <h2>Iniciar sesion</h2>
              </div>
              <span className="qapaq-lock">
                <ShieldCheck size={22} strokeWidth={2.2} />
              </span>
            </div>

            <form className="qapaq-form" onSubmit={onSubmit}>
              <div className="qapaq-field">
                <label htmlFor="tarjeta">Nro. de tarjeta de ahorros</label>
                <div className="qapaq-control">
                  <CreditCard size={17} strokeWidth={1.9} />
                  <input
                    id="tarjeta"
                    value={tarjeta}
                    onChange={(e) => setTarjeta(e.target.value)}
                    placeholder="Ingresa tu usuario"
                    autoComplete="username"
                    autoFocus
                    required
                  />
                </div>
              </div>

              <div className="qapaq-field">
                <label htmlFor="dni">DNI</label>
                <div className="qapaq-control">
                  <Fingerprint size={17} strokeWidth={1.9} />
                  <input
                    id="dni"
                    value={dni}
                    onChange={(e) => setDni(e.target.value.replace(/\D/g, ''))}
                    placeholder="8 digitos"
                    inputMode="numeric"
                    maxLength={8}
                    autoComplete="off"
                    required
                  />
                </div>
              </div>

              <div className="qapaq-field">
                <label htmlFor="password">Clave de Internet</label>
                <div className="qapaq-control">
                  <Lock size={17} strokeWidth={1.9} />
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Ingresa tu clave"
                    autoComplete="current-password"
                    required
                  />
                </div>
              </div>

              <div className="qapaq-form__row">
                <label className="qapaq-check">
                  <input type="checkbox" checked={recordar} onChange={(e) => setRecordar(e.target.checked)} />
                  Recordar sesion
                </label>
                <button className="qapaq-link" type="button">
                  Olvidaste tu clave?
                </button>
              </div>

              {error && <div className="hb-alert hb-alert-error">{error}</div>}

              <button className="qapaq-submit" type="submit" disabled={loading}>
                <Lock size={16} strokeWidth={2.4} />
                {loading ? 'Ingresando...' : 'Ingresar'}
                <ArrowRight size={17} strokeWidth={2.4} />
              </button>

              <p className="qapaq-login-card__hint">
                Usa las credenciales asignadas para tu entorno de pruebas.
              </p>

              <div className="qapaq-form__actions">
                <button type="button">
                  <UserRound size={15} />
                  Registrarme
                </button>
                <Link to="/">
                  <ArrowLeft size={15} />
                  Volver al inicio
                </Link>
              </div>
            </form>
          </div>
        </section>

        <section className="qapaq-promo" aria-label="Portada Home Banking QAPAQ">
          <img src={portadaLogin} alt="Bienvenido a la banca electronica de QAPAQ" />
        </section>
      </main>
    </div>
  )
}
