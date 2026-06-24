import { FileClock } from 'lucide-react'
import { formatDate, toNumber } from '../../utils/format.js'
import Card from '../ui/Card.jsx'
import Tabla from '../ui/Tabla.jsx'
import Loader from '../ui/Loader.jsx'
import Money from '../ui/Money.jsx'
import Badge from '../ui/Badge.jsx'
import Alert from '../ui/Alert.jsx'

export default function HistorialPrestamos({ historial, loading, error }) {
  const columns = [
    { key: 'tipo_registro', header: 'Origen', render: (r) => tipoLabel(r.tipo_registro) },
    { key: 'codigo', header: 'Codigo', render: (r) => <strong>{r.codigo}</strong> },
    { key: 'fecha', header: 'Fecha', render: (r) => formatDate(r.fecha) },
    { key: 'tipo_credito', header: 'Tipo', render: (r) => r.tipo_credito || 'Credito' },
    { key: 'monto', header: 'Monto', align: 'right', render: (r) => <Money value={r.monto} /> },
    { key: 'cuotas', header: 'Cuotas', align: 'center', render: (r) => cuotasLabel(r) },
    { key: 'pago_pendiente', header: 'Saldo contable', align: 'right', render: (r) => pendienteLabel(r) },
    { key: 'estado', header: 'Estado', render: (r) => <Badge estado={r.estado} tone={estadoTone(r.estado)} /> },
    { key: 'detalle', header: 'Detalle', render: (r) => r.detalle || '-' },
  ]

  return (
    <Card title="Historial de prestamos" icon={<FileClock size={18} />} className="prestamo-history-card">
      {error && <Alert tipo="error">{error}</Alert>}
      {loading ? (
        <Loader text="Cargando historial..." />
      ) : (
        <Tabla
          columns={columns}
          rows={historial}
          rowKey={(r) => `${r.tipo_registro}-${r.codigo}`}
          emptyText="No registra solicitudes ni prestamos."
        />
      )}
    </Card>
  )
}

function tipoLabel(tipo) {
  return tipo === 'CREDITO' ? 'Credito' : 'Solicitud'
}

function cuotasLabel(row) {
  if (row.total_cuotas === null || row.total_cuotas === undefined) return '-'
  if (row.tipo_registro === 'CREDITO' && toNumber(row.pago_pendiente) > 0) {
    return `Pendientes ${row.cuotas_pendientes ?? 0} / ${row.total_cuotas ?? 0}`
  }
  if (row.tipo_registro === 'CREDITO') {
    return `Pagadas ${row.cuotas_pagadas ?? 0} / ${row.total_cuotas ?? 0}`
  }
  return `${row.cuotas_pagadas ?? 0} / ${row.total_cuotas ?? 0}`
}

function pendienteLabel(row) {
  if (row.tipo_registro !== 'CREDITO') return '-'
  return <Money value={toNumber(row.pago_pendiente)} />
}

function estadoTone(estado) {
  const text = String(estado || '').toLowerCase()
  if (text.includes('rechaz')) return 'red'
  if (text.includes('cancel') || text.includes('aprobad') || text.includes('desembols')) return 'green'
  if (text.includes('evalu') || text.includes('observ')) return 'amber'
  return undefined
}
