import { useNavigate } from 'react-router-dom'
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  Wallet, CreditCard, Send, Receipt, FileText, FilePlus2,
  PiggyBank, ChevronRight, TrendingDown, TrendingUp,
} from 'lucide-react'
import { useHBAuth } from '../hooks/useHBAuth.js'
import { useCuentas } from '../hooks/useCuentas.js'
import { useCreditos } from '../hooks/useCreditos.js'
import useHistorialPrestamos from '../hooks/useHistorialPrestamos.js'
import { simboloMoneda, toNumber } from '../utils/format.js'
import PageLayout from '../components/layout/PageLayout.jsx'
import ActionPanel from '../components/ui/ActionPanel.jsx'
import Card from '../components/ui/Card.jsx'
import Money from '../components/ui/Money.jsx'
import Badge from '../components/ui/Badge.jsx'
import Loader from '../components/ui/Loader.jsx'
import HistorialPrestamos from '../components/cuentas/HistorialPrestamos.jsx'
import perfilMujer from '../assets/images/perfil-mujer.png'
import perfilVaron from '../assets/images/perfil-varon.png.png'

export default function HomePage() {
  const { user } = useHBAuth()
  const navigate = useNavigate()
  const { cuentas, loading: lc } = useCuentas('ahorro')
  const { creditos, loading: lk } = useCreditos()
  const { historial, loading: lh, error: eh } = useHistorialPrestamos()

  const totalAhorro = cuentas.reduce((s, c) => s + toNumber(c.saldo), 0)
  const totalDeuda = creditos.reduce((s, c) => s + toNumber(c.pago_pendiente), 0)
  const perfil = imagenPerfil(user)
  const balanceData = [
    { name: 'Ahorros', value: totalAhorro, color: '#16a34a' },
    { name: 'Deuda', value: totalDeuda, color: '#e2132b' },
  ].filter((item) => item.value > 0)
  const productosData = [
    { name: 'Ahorros', cantidad: cuentas.length, color: '#16a34a' },
    { name: 'Creditos', cantidad: creditos.length, color: '#e2132b' },
  ]

  const acciones = [
    { icon: Send, label: 'Transferencias propias', to: '/operaciones/transferencia' },
    { icon: Receipt, label: 'Pago de credito', to: '/operaciones/pago-credito' },
    { icon: FileText, label: 'Pago de servicios', to: '/operaciones/pago-servicios' },
    { icon: FilePlus2, label: 'Solicitar prestamo', to: '/creditos/solicitar' },
  ]

  return (
    <PageLayout aside={<ActionPanel title="Operaciones frecuentes" items={acciones} />}>
      <div className="hb-dashboard">
        <div className="dashboard-head hb-dashboard-head">
          <div className="hb-dashboard-greeting">
            <span className="hb-dashboard-profile">
              <img src={perfil} alt="Perfil de cliente" />
            </span>
            <div>
              <h1 className="page-title">Hola {primerNombre(user?.nombre)}</h1>
              <p className="page-subtitle">Esta es la posicion global de tus productos en QAPAQ.</p>
            </div>
          </div>
          <span className="hb-dashboard-user">{user?.codcliente || 'Cliente'}</span>
        </div>

        <div className="grid grid-kpi hb-dashboard-kpis">
          <div className="kpi-card hb-dashboard-kpi" style={{ '--kpi-color': '#16a34a' }}>
            <span className="bbva-kpi-ico" style={{ background: '#dcfce7', color: '#16a34a' }}>
              <PiggyBank size={22} />
            </span>
            <div>
              <span className="kpi-card__label"><TrendingUp size={13} /> Total en ahorros</span>
              <Money className="kpi-card__value" value={totalAhorro} />
              <small>{cuentas.length} cuenta(s)</small>
            </div>
          </div>

          <div className="kpi-card hb-dashboard-kpi" style={{ '--kpi-color': '#e2132b' }}>
            <span className="bbva-kpi-ico" style={{ background: '#fde8eb', color: 'var(--hb-red)' }}>
              <CreditCard size={22} />
            </span>
            <div>
              <span className="kpi-card__label"><TrendingDown size={13} /> Saldo contable de creditos</span>
              <Money className="kpi-card__value" value={totalDeuda} />
              <small>{creditos.length} credito(s)</small>
            </div>
          </div>
        </div>

        <div className="hb-dashboard-charts">
          <section className="hb-chart-card">
            <div className="hb-chart-head">
              <h2>Balance general</h2>
              <p>Ahorros disponibles frente a deuda pendiente.</p>
            </div>
            <div className="hb-chart-body">
              {balanceData.length === 0 ? (
                <p className="bbva-empty">Sin datos para graficar.</p>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={balanceData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={62}
                      outerRadius={92}
                      paddingAngle={5}
                    >
                      {balanceData.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => moneyLabel(value)} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
            <div className="hb-chart-legend">
              {balanceData.map((item) => (
                <span key={item.name}>
                  <i style={{ background: item.color }} />
                  {item.name}: {moneyLabel(item.value)}
                </span>
              ))}
            </div>
          </section>

          <section className="hb-chart-card">
            <div className="hb-chart-head">
              <h2>Productos activos</h2>
              <p>Cantidad de cuentas y creditos registrados.</p>
            </div>
            <div className="hb-chart-body">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={productosData} margin={{ top: 14, right: 12, left: -18, bottom: 0 }}>
                  <XAxis dataKey="name" axisLine={false} tickLine={false} />
                  <YAxis allowDecimals={false} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: '#fff8c2' }} />
                  <Bar dataKey="cantidad" radius={[10, 10, 0, 0]}>
                    {productosData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>

        <Card
          title="Cuentas de Ahorro"
          icon={<Wallet size={18} />}
          className="hb-dashboard-card"
          actions={<button className="bbva-link" onClick={() => navigate('/cuentas/ahorro')}>Ver todas <ChevronRight size={14} /></button>}
        >
          {lc ? <Loader text="Cargando cuentas..." /> : cuentas.length === 0 ? (
            <p className="bbva-empty">No registra cuentas de ahorro.</p>
          ) : (
            <ul className="bbva-prodlist">
              {cuentas.map((c) => (
                <li key={c.codcuentaahorro} onClick={() => navigate(`/cuentas/ahorro/${c.codcuentaahorro}/movimientos`)}>
                  <div className="bbva-prod-info">
                    <strong>{c.codcuentaahorro}</strong>
                    <small>{c.tipo} - <Badge estado={c.estado} /></small>
                  </div>
                  <div className="bbva-prod-amt">
                    <Money value={c.saldo} simbolo={simboloMoneda(c.moneda)} />
                    <ChevronRight size={16} />
                  </div>
                </li>
              ))}
              <li className="bbva-prodlist-total">
                <span>Saldo disponible total</span>
                <Money value={totalAhorro} className="bbva-money-strong" />
              </li>
            </ul>
          )}
        </Card>

        <Card
          title="Prestamos"
          icon={<CreditCard size={18} />}
          className="hb-dashboard-card"
          actions={<button className="bbva-link" onClick={() => navigate('/cuentas/credito')}>Ver todos <ChevronRight size={14} /></button>}
        >
          {lk ? <Loader text="Cargando creditos..." /> : creditos.length === 0 ? (
            <p className="bbva-empty">No registra creditos vigentes.</p>
          ) : (
            <ul className="bbva-prodlist">
              {creditos.map((c) => (
                <li key={c.codcuentacredito} onClick={() => navigate(`/cuentas/credito/${c.codcuentacredito}/cuotas`)}>
                  <div className="bbva-prod-info">
                    <strong>{c.codcuentacredito}</strong>
                    <small>{c.tipo_credito || c.producto || 'Credito'} - <Badge estado={c.calificacion || 'Normal'} tone={c.dias_atraso > 0 ? 'red' : undefined} /></small>
                    <small>
                      Prestamo original <Money value={c.monto_aprobado} /> - {cuotasResumen(c)}
                    </small>
                  </div>
                  <div className="bbva-prod-amt">
                    <Money value={c.pago_pendiente} />
                    <ChevronRight size={16} />
                  </div>
                </li>
              ))}
              <li className="bbva-prodlist-total">
                <span>Saldo contable total</span>
                <Money value={totalDeuda} className="bbva-money-strong" />
              </li>
            </ul>
          )}
        </Card>

        <HistorialPrestamos historial={historial} loading={lh} error={eh} />
      </div>
    </PageLayout>
  )
}

function primerNombre(nombre) {
  if (!nombre) return 'Cliente'
  const parts = nombre.split(',')
  const np = (parts[1] || parts[0]).trim().split(/\s+/)[0]
  return np || 'Cliente'
}

function imagenPerfil(user) {
  const sexo = String(user?.sexo || '').trim().toUpperCase()
  if (sexo === 'F') return perfilMujer
  if (sexo === 'M') return perfilVaron

  const nombre = primerNombre(user?.nombre).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
  const nombresMujer = new Set(['maria', 'ana', 'laura', 'rosa', 'carmen', 'elena', 'lucia', 'sofia', 'valeria'])
  return nombresMujer.has(nombre) ? perfilMujer : perfilVaron
}

function moneyLabel(value) {
  return new Intl.NumberFormat('es-PE', {
    style: 'currency',
    currency: 'PEN',
    minimumFractionDigits: 2,
  }).format(Number(value || 0))
}

function cuotasResumen(credito) {
  const total = Number(credito.total_cuotas || 0)
  const pendientes = Number(credito.cuotas_pendientes || 0)
  const pagadas = Number(credito.cuotas_pagadas || 0)
  if (toNumber(credito.pago_pendiente) > 0) {
    return `cuotas pendientes ${pendientes}/${total}`
  }
  return `cuotas pagadas ${pagadas}/${total}`
}
