import { useEffect, useRef, useState } from 'react'
import { buscarClientes } from '../../services/svc_clientes.js'
import { money } from '../../utils/format.js'

export default function ClienteSearch({ value, onChange, onSelect, required = true }) {
  const [query, setQuery] = useState(value || '')
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const boxRef = useRef(null)

  useEffect(() => {
    setQuery(value || '')
  }, [value])

  useEffect(() => {
    const handleClick = (event) => {
      if (!boxRef.current?.contains(event.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  useEffect(() => {
    const term = query.trim()
    if (term.length < 2) {
      setItems([])
      return
    }

    let alive = true
    setLoading(true)
    const timer = setTimeout(async () => {
      try {
        const data = await buscarClientes(term)
        if (alive) {
          setItems(data)
          setOpen(true)
        }
      } catch {
        if (alive) setItems([])
      } finally {
        if (alive) setLoading(false)
      }
    }, 250)

    return () => {
      alive = false
      clearTimeout(timer)
    }
  }, [query])

  function choose(cliente) {
    const cod = String(cliente.codcliente || '').trim()
    setQuery(cod)
    setOpen(false)
    onChange(cod)
    onSelect?.(cliente)
  }

  return (
    <div className="client-search" ref={boxRef}>
      <input
        type="text"
        value={query}
        onFocus={() => items.length > 0 && setOpen(true)}
        onChange={(e) => {
          setQuery(e.target.value)
          onChange(e.target.value)
        }}
        placeholder="Buscar por código, nombre o DNI"
        required={required}
        autoComplete="off"
      />
      {open && (
        <div className="client-search__menu">
          {loading && <div className="client-search__empty">Buscando...</div>}
          {!loading && items.length === 0 && (
            <div className="client-search__empty">Sin resultados</div>
          )}
          {!loading && items.map((cliente) => (
            <button
              type="button"
              key={cliente.codcliente}
              className="client-search__item"
              onClick={() => choose(cliente)}
            >
              <strong>{cliente.codcliente}</strong>
              <span>{cliente.nomcliente}</span>
              <small>
                DNI {cliente.numerodocumentoidentidad || '-'} · ingreso {money(cliente.montoingresoneto || 0)}
              </small>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
