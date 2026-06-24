import { useNavigate } from 'react-router-dom'
import { Lock, Menu, Phone, Search } from 'lucide-react'
import Logo from '../ui/Logo.jsx'

export default function PublicHeader() {
  const navigate = useNavigate()

  return (
    <header className="qweb-header">
      <div className="qweb-topbar">
        <div className="qweb-topbar__inner">
          <span>
            <Phone size={14} />
            (01) 712 3223
          </span>
          <nav aria-label="Enlaces superiores">
            <a href="#footer">Transparencia</a>
            <a href="#footer">Mapa del Sitio</a>
            <a href="#footer">
              <Search size={14} />
              Buscar
            </a>
          </nav>
        </div>
      </div>

      <div className="qweb-mainbar">
        <button className="qweb-brand" onClick={() => navigate('/')} aria-label="QAPAQ inicio">
          <Logo size={66} />
        </button>

        <div className="qweb-mainbar__actions">
          <button className="qweb-access qweb-access--dark" onClick={() => navigate('/login')}>
            <Lock size={16} />
            Qapaq por INTERNET
          </button>
          <button className="qweb-access qweb-access--outline" onClick={() => navigate('/login')}>
            Abre tu CUENTA
          </button>
          <button className="qweb-access qweb-access--red" onClick={() => navigate('/login')}>
            Solicita tu PRESTAMO
          </button>
        </div>

        <button className="qweb-menu-btn" onClick={() => navigate('/login')} aria-label="Menu">
          <Menu size={24} />
        </button>
      </div>
    </header>
  )
}
