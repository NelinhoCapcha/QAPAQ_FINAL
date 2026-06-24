import { useCallback, useEffect, useState } from 'react'
import { getHistorialPrestamos } from '../services/creditosService.js'
import { extractError } from '../utils/format.js'

export default function useHistorialPrestamos() {
  const [historial, setHistorial] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const cargar = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setHistorial(await getHistorialPrestamos())
    } catch (err) {
      setError(extractError(err, 'No se pudo cargar el historial de prestamos.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    cargar()
  }, [cargar])

  return { historial, loading, error, recargar: cargar }
}
