import { useState } from 'react'
import { useProductos } from '../../hooks/useProductos.js'
import ClienteSearch from './ClienteSearch.jsx'

const VACIO = {
  codcliente: '',
  codtipocredito: 'ME',
  montosolicitud: '',
  plazo: '',
  montoingresoneto: '',
  codactividadeconomica: '',
  codasesor: '',
}

export default function SolicitudForm({ onSubmit, loading, codasesorDefault }) {
  const [form, setForm] = useState({ ...VACIO, codasesor: codasesorDefault ?? '' })
  const { productos, loading: loadingProductos } = useProductos()

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({
      codcliente: String(form.codcliente).trim(),
      montosolicitud: Number(form.montosolicitud),
      plazo: Number(form.plazo),
      codtipocredito: form.codtipocredito,
      codactividadeconomica: String(form.codactividadeconomica).trim(),
      montoingresoneto: Number(form.montoingresoneto),
      codasesor: String(form.codasesor).trim(),
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <h4 style={{ marginTop: 0 }}>Datos de la solicitud</h4>
      <div className="form-grid">
        <div className="field">
          <label>Cliente</label>
          <ClienteSearch
            value={form.codcliente}
            onChange={(value) => set('codcliente', value)}
            onSelect={(cliente) => {
              set('codcliente', cliente.codcliente)
              if (cliente.montoingresoneto) set('montoingresoneto', cliente.montoingresoneto)
            }}
          />
        </div>
        <div className="field">
          <label>Tipo de credito</label>
          <select value={form.codtipocredito} onChange={(e) => set('codtipocredito', e.target.value)} disabled={loadingProductos}>
            {loadingProductos ? (
              <option>Cargando...</option>
            ) : (
              productos.map((p) => (
                <option key={p.codtipocredito} value={p.codtipocredito}>
                  {p.descripcion}
                </option>
              ))
            )}
          </select>
        </div>
        <div className="field">
          <label>Monto solicitado</label>
          <input type="number" step="0.01" value={form.montosolicitud} onChange={(e) => set('montosolicitud', e.target.value)} required />
        </div>
        <div className="field">
          <label>Plazo (meses)</label>
          <input type="number" value={form.plazo} onChange={(e) => set('plazo', e.target.value)} required />
        </div>
        <div className="field">
          <label>Ingreso neto mensual</label>
          <input type="number" step="0.01" value={form.montoingresoneto} onChange={(e) => set('montoingresoneto', e.target.value)} required />
        </div>
        <div className="field">
          <label>Actividad economica (CIIU)</label>
          <input type="text" value={form.codactividadeconomica} onChange={(e) => set('codactividadeconomica', e.target.value)} placeholder="Ej. 4711" required />
        </div>
        <div className="field">
          <label>Codigo de asesor</label>
          <input type="text" value={form.codasesor} onChange={(e) => set('codasesor', e.target.value)} required />
        </div>
      </div>

      <button className="btn" type="submit" disabled={loading} style={{ marginTop: 20 }}>
        {loading ? 'Evaluando...' : 'Crear solicitud'}
      </button>
    </form>
  )
}
