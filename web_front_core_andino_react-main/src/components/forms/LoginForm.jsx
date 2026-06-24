import { ArrowRight, Lock, User } from 'lucide-react'
import { useState } from 'react'

export default function LoginForm({ onSubmit, loading, error }) {
  const [numerodni, setNumerodni] = useState('')
  const [password, setPassword] = useState('')
  const [recordar, setRecordar] = useState(true)

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit(numerodni.trim(), password)
  }

  return (
    <form className="qapaq-form" onSubmit={handleSubmit}>
      <div className="qapaq-field">
        <label htmlFor="dni">DNI del personal</label>
        <div className="qapaq-control">
          <User size={17} strokeWidth={1.9} />
          <input
            id="dni"
            type="text"
            value={numerodni}
            onChange={(e) => setNumerodni(e.target.value)}
            placeholder="Ingresa tu DNI"
            autoComplete="username"
            autoFocus
            required
          />
        </div>
      </div>

      <div className="qapaq-field">
        <label htmlFor="pwd">Contrasena</label>
        <div className="qapaq-control">
          <Lock size={17} strokeWidth={1.9} />
          <input
            id="pwd"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Ingresa tu contrasena"
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
          Olvidaste tu contrasena?
        </button>
      </div>

      {error && <div className="alert alert--error">{error}</div>}

      <button className="qapaq-submit" type="submit" disabled={loading}>
        <Lock size={16} strokeWidth={2.4} />
        {loading ? 'Ingresando...' : 'Ingresar'}
        <ArrowRight size={17} strokeWidth={2.4} />
      </button>

      <div className="qapaq-form__actions">
        <button type="button">Registrarme</button>
        <button type="button">Necesito ayuda</button>
      </div>
    </form>
  )
}
