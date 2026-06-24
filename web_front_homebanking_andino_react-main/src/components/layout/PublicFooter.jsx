import { Facebook, Instagram, Phone, Play, ReceiptText, Send, Music2 } from 'lucide-react'

const FOOTER_COLS = [
  {
    title: 'QAPAQ',
    links: ['Conocenos', 'Ubicanos', 'Trabaja con Nosotros', 'Memorias y EEFF', 'Mapa del Sitio'],
  },
  {
    title: 'Informacion de interes',
    links: ['Terminos y Condiciones', 'Proteccion de Datos Personales', 'Constancia de No Adeudo', 'Guia para el Cliente', 'Enlaces de Interes'],
  },
  {
    title: 'Transparencia',
    links: ['Informacion de Reclamos', 'Estadistica de Reclamos', 'Comunicados', 'Campanas'],
  },
]

export default function PublicFooter() {
  return (
    <footer className="qweb-footer" id="footer">
      <div className="qweb-footer__inner">
        <div className="qweb-footer__brand">
          <strong className="qweb-footer__logo">QAPAQ</strong>
          <p>Financiera QAPAQ. Soluciones de ahorro, prestamos y canales digitales para acompanar tus metas.</p>
          <a className="qweb-claim" href="#footer">
            <ReceiptText size={22} />
            Libro de reclamaciones
          </a>
        </div>

        {FOOTER_COLS.map((col) => (
          <div className="qweb-footer__col" key={col.title}>
            <h3>{col.title}</h3>
            <ul>
              {col.links.map((link) => (
                <li key={link}>
                  <a href="#footer">{link}</a>
                </li>
              ))}
            </ul>
          </div>
        ))}

        <div className="qweb-footer__contact">
          <h3>Contactanos</h3>
          <div className="qweb-social">
            <a href="#footer" aria-label="Facebook"><Facebook size={18} /></a>
            <a href="#footer" aria-label="YouTube"><Play size={18} /></a>
            <a href="#footer" aria-label="Telefono"><Phone size={18} /></a>
            <a href="#footer" aria-label="Instagram"><Instagram size={18} /></a>
            <a href="#footer" aria-label="TikTok"><Music2 size={18} /></a>
          </div>
          <div className="qweb-call">
            <span>Call Center:</span>
            <strong>+51 1 7123223</strong>
            <small>Lun-Sab de 9am a 9pm</small>
          </div>
          <a className="qweb-whatsapp" href="#footer">
            <Send size={16} />
            Escribenos
          </a>
        </div>
      </div>

      <div className="qweb-footer__legal">
        © Financiera QAPAQ S.A. | 20521308321
      </div>
    </footer>
  )
}
