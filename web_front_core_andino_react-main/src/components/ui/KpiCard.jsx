/**
 * Tarjeta de indicador. valor + label + color de borde opcional.
 */
export default function KpiCard({ label, valor, color, sufijo = '' }) {
  const style = color ? { '--kpi-color': color } : undefined

  return (
    <div className="kpi-card" style={style}>
      <div className="kpi-card__label">{label}</div>
      <div className="kpi-card__value" style={color ? { color } : undefined}>
        {valor}
        {sufijo}
      </div>
    </div>
  )
}
