import api from './svc_api.js'

/**
 * GET /clientes/{codcliente}
 * @returns {Promise<Object>} ClienteOut
 */
export async function getCliente(codcliente) {
  const { data } = await api.get(`/clientes/${codcliente}`)
  return data
}

/**
 * GET /clientes?search=
 * Busca por código, nombre o documento.
 */
export async function buscarClientes(search, limit = 12) {
  const { data } = await api.get('/clientes', {
    params: { search, limit },
  })
  return data
}
