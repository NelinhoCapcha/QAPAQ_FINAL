import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, CalendarDays, Receipt, RefreshCw } from 'lucide-react'
import { useCuotas } from '../hooks/useCreditos.js'
import { formatDate } from '../utils/format.js'
import PageLayout from '../components/layout/PageLayout.jsx'
import Card from '../components/ui/Card.jsx'
import Tabla from '../components/ui/Tabla.jsx'
import Loader from '../components/ui/Loader.jsx'
import Money from '../components/ui/Money.jsx'
import Badge from '../components/ui/Badge.jsx'
import Alert from '../components/ui/Alert.jsx'

export default function CuotasCreditoPage() {
  const { cod } = useParams()
  const navigate = useNavigate()
  const { cuotas, loading, error, recargar } = useCuotas(cod)

  const proxima = cuotas.find((c) => !c.pagada)
  const pagadas = cuotas.filter((c) => c.pagada)
  const pendientes = cuotas.filter((c) => !c.pagada)
  const totalCuotasCredito = Number(cuotas.find((c) => c.total_cuotas)?.total_cuotas || cuotas.length)
  const pendientesCredito = Math.max(totalCuotasCredito - pagadas.length, 0)
  const totalPendiente = pendientes.reduce((s, c) => s + Number(c.total_informativo || c.monto_cuota || 0), 0)

  const columns = [
    { key: 'nrocuota', header: 'Nro. cuota', render: (c) => <strong>{c.nrocuota}</strong> },
    { key: 'fecha_vencimiento', header: 'Vencimiento', render: (c) => formatDate(c.fecha_vencimiento) },
    { key: 'saldo_principal_antes', header: 'Saldo principal antes', align: 'right', render: (c) => <Money value={saldoAntes(c)} /> },
    { key: 'capital_programado', header: 'Capital', align: 'right', render: (c) => <Money value={c.capital_programado ?? c.monto_cuota} /> },
    { key: 'interes_programado', header: 'Interes', align: 'right', render: (c) => <Money value={c.interes_programado} /> },
    { key: 'seguro_desgravamen', header: 'Seguro', align: 'right', render: (c) => <Money value={c.seguro_desgravamen} /> },
    { key: 'itf_estimado', header: 'ITF', align: 'right', render: (c) => <Money value={c.itf_estimado} /> },
    { key: 'total_informativo', header: 'Total ref.', align: 'right', className: 'cuota-total-ref', render: (c) => <Money value={c.total_informativo ?? c.monto_cuota} /> },
    { key: 'monto_saldo', header: 'Saldo capital despues', align: 'right', render: (c) => <Money value={c.monto_saldo} /> },
    { key: 'dias_atraso', header: 'Dias vencida', align: 'center', render: (c) => (diasVencida(c) > 0 ? <Badge estado={`${diasVencida(c)} dias`} tone="red" /> : '0') },
    { key: 'estado', header: 'Estado de pago', render: (c) => <Badge estado={estadoCuota(c)} tone={toneCuota(c)} /> },
  ]

  return (
    <PageLayout className="credito-cuotas-page">
      <button className="hb-back" onClick={() => navigate('/cuentas/credito')}>
        <ArrowLeft size={16} /> Volver a Prestamos
      </button>

      <div className="bbva-page-head">
        <div>
          <h1 className="bbva-page-title">Cronograma de cuotas</h1>
          <p className="bbva-page-sub">Prestamos - Credito {cod}</p>
        </div>
        <div className="bbva-page-actions">
          <button className="bbva-btn-ghost" onClick={recargar} disabled={loading}>
            <RefreshCw size={14} /> Actualizar
          </button>
          <button className="bbva-btn" onClick={() => navigate(`/operaciones/pago-credito/${cod}`)} disabled={!proxima}>
            <Receipt size={14} /> Pagar proxima cuota
          </button>
        </div>
      </div>

      {error && <Alert tipo="error">{error}</Alert>}

      {proxima && (
        <Alert tipo="info">
          Proxima cuota pendiente por pagar: <strong>Nro. {proxima.nrocuota}</strong> - vence el{' '}
          <strong>{formatDate(proxima.fecha_vencimiento)}</strong> - total referencial <Money value={proxima.total_informativo ?? proxima.monto_cuota} />.
        </Alert>
      )}

      <div className="credito-cuotas-summary">
        <div>
          <span>Cuotas pagadas</span>
          <strong>{pagadas.length} / {totalCuotasCredito}</strong>
        </div>
        <div>
          <span>Cuotas pendientes</span>
          <strong>{pendientesCredito}</strong>
        </div>
        <div>
          <span>Cuotas en tabla</span>
          <strong>{cuotas.length}</strong>
        </div>
        <div>
          <span>Total cuotas ref.</span>
          <strong><Money value={totalPendiente} /></strong>
        </div>
      </div>

      <Card title="Cronograma de pagos" icon={<CalendarDays size={18} />} className="credito-cuotas-card">
        <p className="credito-cuotas-help">
          Cada fila separa capital, interes, seguro de desgravamen e ITF referencial. Solo el capital reduce
          el saldo del credito; los demas importes son costos de la cuota. El total ref. es una proyeccion de
          pagos futuros, no el saldo contable mostrado en Mis creditos. Esta tabla muestra {cuotas.length}
          cuotas cargadas en cronograma de un total de {totalCuotasCredito}.
        </p>

        {loading ? (
          <Loader text="Cargando cronograma..." />
        ) : (
          <Tabla
            columns={columns}
            rows={cuotas}
            rowKey={(c) => c.nrocuota}
            emptyText="Este credito no tiene cuotas registradas o ya fue cancelado."
          />
        )}
      </Card>
    </PageLayout>
  )
}

function estadoCuota(c) {
  if (c.pagada) return 'Pagada'
  if (estaVencida(c.fecha_vencimiento) || c.estado === '02') return 'Pendiente vencida'
  return 'Pendiente por pagar'
}

function toneCuota(c) {
  if (c.pagada) return 'green'
  if (estaVencida(c.fecha_vencimiento) || c.estado === '02') return 'red'
  return 'amber'
}

function diasVencida(c) {
  if (c.pagada) return 0
  const venc = parseDateOnly(c.fecha_vencimiento)
  if (!venc) return Number(c.dias_atraso || 0)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diff = Math.floor((today - venc) / 86400000)
  return Math.max(Number(c.dias_atraso || 0), diff, 0)
}

function estaVencida(fecha) {
  const venc = parseDateOnly(fecha)
  if (!venc) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return venc < today
}

function parseDateOnly(fecha) {
  if (!fecha) return null
  const [y, m, d] = String(fecha).slice(0, 10).split('-').map(Number)
  if (!y || !m || !d) return null
  return new Date(y, m - 1, d)
}

function saldoAntes(c) {
  return Number(c.monto_saldo || 0) + Number(c.capital_programado ?? c.monto_cuota ?? 0)
}
