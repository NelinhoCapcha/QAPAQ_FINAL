import { CalendarClock, Lock, PiggyBank, Landmark } from 'lucide-react'
import { formatDate, formatTEA } from '../../utils/format.js'
import Money from '../ui/Money.jsx'
import Tabla from '../ui/Tabla.jsx'
import Loader from '../ui/Loader.jsx'
import Alert from '../ui/Alert.jsx'
import Badge from '../ui/Badge.jsx'

export default function DetalleAhorro({ detalle, loading, error }) {
  if (loading) return <Loader text="Cargando detalle..." />
  if (error) return <Alert tipo="error">{error}</Alert>
  if (!detalle) return null

  const { codtipo } = detalle

  if (codtipo === 'PF' && detalle.plazo_fijo) return <PlazoFijo d={detalle.plazo_fijo} />
  if (codtipo === 'CT' && detalle.cts) return <Cts d={detalle.cts} />
  if (codtipo === 'AP' && detalle.ahorro_programado) return <AhorroProgramado d={detalle.ahorro_programado} />

  return (
    <div className="bbva-detalle">
      <p className="bbva-empty" style={{ margin: 0 }}>
        {detalle.mensaje || 'Esta cuenta no tiene detalle de subproducto adicional.'}
      </p>
    </div>
  )
}

function PlazoFijo({ d }) {
  return (
    <div className="bbva-detalle bbva-detalle-ahorro">
      <h4 className="bbva-detalle-title"><CalendarClock size={16} /> Deposito a Plazo Fijo</h4>
      <dl className="hb-dl">
        <div><dt>Vigencia</dt><dd>{formatDate(d.fecha_vigencia)}</dd></div>
        <div><dt>Plazo</dt><dd>{d.nro_dias_plazo} dias</dd></div>
        <div><dt>Saldo capital</dt><dd><Money value={d.saldo_capital} /></dd></div>
        <div><dt>Tasa pagada</dt><dd>{formatTEA(d.tasa_pagada)}</dd></div>
        <div><dt>Interes pactado</dt><dd><Money value={d.interes_pactado} /></dd></div>
        <div><dt>Interes devengado</dt><dd><Money value={d.interes_devengado} /></dd></div>
        <div><dt>Interes pagado</dt><dd><Money value={d.interes_pagado} /></dd></div>
        <div><dt>Renovaciones</dt><dd>{d.nro_renovaciones}</dd></div>
      </dl>
    </div>
  )
}

function Cts({ d }) {
  return (
    <div className="bbva-detalle bbva-detalle-ahorro">
      <h4 className="bbva-detalle-title"><Lock size={16} /> Cuenta CTS</h4>
      <dl className="hb-dl">
        <div><dt>Capital</dt><dd><Money value={d.capital} /></dd></div>
        <div><dt>Interes</dt><dd><Money value={d.interes} /></dd></div>
        <div><dt>Capital intangible</dt><dd><Money value={d.capital_intangible} /></dd></div>
        <div><dt>Interes intangible</dt><dd><Money value={d.interes_intangible} /></dd></div>
      </dl>
      <div className="bbva-cts-disp">
        <span><Landmark size={16} /> Disponible para retiro por ley</span>
        <Money value={d.disponible} className="bbva-money-strong" />
      </div>
    </div>
  )
}

function AhorroProgramado({ d }) {
  const cols = [
    { key: 'coddeposito', header: 'Deposito' },
    { key: 'fecha_programada', header: 'Fecha programada', render: (r) => formatDate(r.fecha_programada) },
    { key: 'fecha_efectuada', header: 'Fecha efectuada', render: (r) => formatDate(r.fecha_efectuada) },
    { key: 'monto_cuota', header: 'Monto cuota', align: 'right', render: (r) => <Money value={r.monto_cuota} /> },
    { key: 'monto_amortizado', header: 'Amortizado', align: 'right', render: (r) => <Money value={r.monto_amortizado} /> },
    { key: 'dias_retraso', header: 'Dias retraso', align: 'center', render: (r) => (r.dias_retraso > 0 ? <Badge estado={`${r.dias_retraso}`} tone="red" /> : '0') },
    { key: 'depositada', header: 'Estado', render: (r) => <Badge estado={r.depositada ? 'Depositada' : 'Pendiente'} /> },
  ]

  return (
    <div className="bbva-detalle bbva-detalle-ahorro">
      <h4 className="bbva-detalle-title"><PiggyBank size={16} /> Ahorro Programado</h4>
      <dl className="hb-dl ahorro-summary">
        <div><dt>Capital acumulado</dt><dd><Money value={d.capital} /></dd></div>
        <div><dt>Cuota</dt><dd><Money value={d.monto_cuota} /></dd></div>
        <div><dt>Nro. de cuotas</dt><dd>{d.nro_cuotas}</dd></div>
        <div><dt>Tasa incentivo</dt><dd>{formatTEA(d.tasa_incentivo)}</dd></div>
        <div><dt>Vigencia</dt><dd>{formatDate(d.fecha_vigencia)}</dd></div>
      </dl>
      <h5 className="bbva-detalle-sub ahorro-schedule-title">Cronograma de depositos</h5>
      <div className="ahorro-schedule">
        <Tabla
          columns={cols}
          rows={d.cronograma || []}
          rowKey={(r) => r.coddeposito}
          emptyText="Sin cronograma de depositos."
        />
      </div>
    </div>
  )
}
