import { useNavigate } from 'react-router-dom'
import { CreditCard, ListChecks, RefreshCw, Receipt, FilePlus2, Percent, AlertTriangle, Landmark, CalendarCheck2 } from 'lucide-react'
import { useCreditos } from '../hooks/useCreditos.js'
import useHistorialPrestamos from '../hooks/useHistorialPrestamos.js'
import { formatDate, toNumber } from '../utils/format.js'
import PageLayout from '../components/layout/PageLayout.jsx'
import ActionPanel from '../components/ui/ActionPanel.jsx'
import Card from '../components/ui/Card.jsx'
import Tabla from '../components/ui/Tabla.jsx'
import Loader from '../components/ui/Loader.jsx'
import Money from '../components/ui/Money.jsx'
import Badge from '../components/ui/Badge.jsx'
import Alert from '../components/ui/Alert.jsx'
import HistorialPrestamos from '../components/cuentas/HistorialPrestamos.jsx'

export default function CuentasCreditoPage() {
  const { creditos, loading, error, recargar } = useCreditos()
  const { historial, loading: lh, error: eh } = useHistorialPrestamos()
  const navigate = useNavigate()

  const totalDeuda = creditos.reduce((s, c) => s + toNumber(c.pago_pendiente), 0)
  const totalPrestado = creditos.reduce((s, c) => s + toNumber(c.monto_aprobado), 0)
  const totalInteres = creditos.reduce((s, c) => s + toNumber(c.saldo_interes), 0)
  const totalMoraGasto = creditos.reduce((s, c) => s + toNumber(c.saldo_moratorio) + toNumber(c.saldo_gasto), 0)
  const totalItf = creditos.reduce((s, c) => s + toNumber(c.itf_estimado_cancelacion), 0)
  const cuotasPendientes = creditos.reduce((s, c) => s + Number(c.cuotas_pendientes || 0), 0)
  const totalCuotas = creditos.reduce((s, c) => s + Number(c.total_cuotas || 0), 0)

  const acciones = [
    { icon: Receipt, label: 'Pago de credito', to: '/operaciones/pago-credito' },
    { icon: FilePlus2, label: 'Solicitar prestamo', to: '/creditos/solicitar' },
  ]

  const columns = [
    { key: 'codcuentacredito', header: 'Tipo y numero', render: (r) => (
      <div className="bbva-cell-prod credito-prod-cell">
        <strong>{r.codcuentacredito}</strong>
        <small>{r.producto || 'Credito'} - {r.tipo_credito || tipoCredito(r.cod_tipo_credito)}</small>
      </div>
    ) },
    { key: 'fecha_desembolso', header: 'Desembolso', render: (r) => formatDate(r.fecha_desembolso) },
    { key: 'monto_aprobado', header: 'Prestamo original', align: 'right', render: (r) => <Money value={r.monto_aprobado} /> },
    { key: 'cuotas', header: 'Cuotas', align: 'center', render: (r) => cuotasLabel(r) },
    { key: 'tasa_compensatoria', header: 'TEA aplicada', align: 'right', render: (r) => pctLabel(r.tasa_compensatoria) },
    { key: 'tasa_moratoria', header: 'Mora anual', align: 'right', render: (r) => pctLabel(r.tasa_moratoria) },
    { key: 'saldo_capital', header: 'Capital', align: 'right', render: (r) => <Money value={r.saldo_capital} /> },
    { key: 'saldo_interes', header: 'Interes', align: 'right', render: (r) => <Money value={r.saldo_interes} /> },
    { key: 'itf_estimado_cancelacion', header: 'ITF ref.', align: 'right', render: (r) => <Money value={r.itf_estimado_cancelacion} /> },
    { key: 'pago_pendiente', header: 'Saldo contable', align: 'right', render: (r) => <Money value={r.pago_pendiente} /> },
    { key: 'dias_atraso', header: 'Dias atraso', align: 'center', render: (r) => (r.dias_atraso > 0 ? <Badge estado={`${r.dias_atraso}`} tone="red" /> : '0') },
    { key: 'calificacion', header: 'Calificacion', render: (r) => <Badge estado={r.calificacion || 'Normal'} tone={r.dias_atraso > 0 ? 'red' : undefined} /> },
    { key: 'cuotas', header: '', align: 'center', render: (r) => (
      <button className="bbva-btn-ghost sm" onClick={() => navigate(`/cuentas/credito/${r.codcuentacredito}/cuotas`)}>
        <ListChecks size={14} /> Ver cuotas
      </button>
    ) },
  ]

  return (
    <PageLayout
      className="credito-products-page"
      title="Prestamos"
      subtitle="Prestamos > Mis productos"
      actions={<button className="bbva-btn-ghost" onClick={recargar} disabled={loading}><RefreshCw size={14} /> Actualizar</button>}
      aside={<ActionPanel title="Operaciones" items={acciones} />}
    >
      {error && <Alert tipo="error">{error}</Alert>}

      {creditos.length > 0 && (
        <div className="credito-info-grid">
          <div className="credito-info-card">
            <Percent size={22} />
            <span>Prestamo original</span>
            <strong><Money value={totalPrestado} /></strong>
          </div>
          <div className="credito-info-card">
            <CalendarCheck2 size={22} />
            <span>Cuotas pendientes</span>
            <strong>{cuotasPendientes} / {totalCuotas}</strong>
          </div>
          <div className="credito-info-card">
            <Percent size={22} />
            <span>Saldo contable total</span>
            <strong><Money value={totalDeuda} /></strong>
          </div>
          <div className="credito-info-card">
            <CreditCard size={22} />
            <span>Interes pendiente</span>
            <strong><Money value={totalInteres} /></strong>
          </div>
          <div className="credito-info-card credito-info-card--warn">
            <AlertTriangle size={22} />
            <span>Mora y gastos</span>
            <strong><Money value={totalMoraGasto} /></strong>
          </div>
          <div className="credito-info-card">
            <Landmark size={22} />
            <span>ITF estimado</span>
            <strong><Money value={totalItf} /></strong>
          </div>
        </div>
      )}

      <Card title="Mis creditos" icon={<CreditCard size={18} />} className="credito-card">
        {loading ? (
          <Loader text="Cargando creditos..." />
        ) : (
          <>
            <p className="credito-help">
              El saldo contable suma capital, interes devengado, mora y gastos registrados a hoy. El total
              referencial del cronograma puede ser mayor porque incluye intereses programados, seguro e ITF
              por cada cuota pendiente.
            </p>
            <Tabla columns={columns} rows={creditos} rowKey={(r) => r.codcuentacredito}
              emptyText="No registra creditos vigentes." />

            {creditos.map((credito) => (
              <div className="credito-rate-note" key={`${credito.codcuentacredito}-note`}>
                <strong>{credito.codcuentacredito}</strong>
                <span>{credito.rango_tea_referencial}</span>
                <small>{credito.recomendacion_mora}</small>
              </div>
            ))}

            {creditos.length > 0 && (
              <div className="bbva-prodlist-total">
                <span>Saldo contable total</span>
                <Money value={totalDeuda} className="bbva-money-strong" />
              </div>
            )}
          </>
        )}
      </Card>

      <HistorialPrestamos historial={historial} loading={lh} error={eh} />
    </PageLayout>
  )
}

function pctLabel(value) {
  if (value === null || value === undefined || value === '') return '-'
  return `${Number(value).toFixed(2)}%`
}

function tipoCredito(cod) {
  if (cod === '01') return 'Microempresa'
  if (cod === '02') return 'Pequena Empresa'
  if (cod === '03') return 'Consumo'
  return 'Credito'
}

function cuotasLabel(credito) {
  const total = Number(credito.total_cuotas || 0)
  if (toNumber(credito.pago_pendiente) > 0) {
    return `Pendientes ${Number(credito.cuotas_pendientes || 0)} / ${total}`
  }
  return `Pagadas ${Number(credito.cuotas_pagadas || 0)} / ${total}`
}
