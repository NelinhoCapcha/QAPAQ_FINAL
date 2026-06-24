import { money } from '../../utils/format.js'

/**
 * Plan de pagos de un credito.
 */
export default function TablaCronograma({ cronograma = [] }) {
  if (!cronograma.length) {
    return <p className="page-subtitle">Sin cronograma disponible.</p>
  }

  const hasSeguro = cronograma.some((q) => q.seguro_desgravamen !== undefined || q.seguro !== undefined)
  const hasItf = cronograma.some((q) => q.itf !== undefined)

  return (
    <table className="tbl">
      <thead>
        <tr>
          <th>#</th>
          <th>Vencimiento</th>
          <th>Pago</th>
          <th className="num">Capital</th>
          <th className="num">Interes</th>
          {hasSeguro && <th className="num">Seguro</th>}
          {hasItf && <th className="num">ITF</th>}
          <th className="num">Cuota</th>
          <th className="num">Saldo</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        {cronograma.map((q) => (
          <tr key={q.nrocuota}>
            <td>{q.nrocuota}</td>
            <td>{q.fechavencimientopagocuota}</td>
            <td>{q.fechapagocuota || 'Pendiente'}</td>
            <td className="num">{money(q.montocapitalprogramado)}</td>
            <td className="num">{money(q.montointeresprogramado)}</td>
            {hasSeguro && <td className="num">{money(q.seguro_desgravamen ?? q.seguro)}</td>}
            {hasItf && <td className="num">{money(q.itf)}</td>}
            <td className="num">{money(q.montocuota)}</td>
            <td className="num">{money(q.montosaldo)}</td>
            <td>{q.pagada ? 'Pagada' : (q.codestadocuota ?? 'Pendiente')}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
