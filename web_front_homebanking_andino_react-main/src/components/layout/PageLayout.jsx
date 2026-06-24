/**
 * Layout de página estilo BBVA: contenido principal a la izquierda y un panel
 * de acciones/accesos a la derecha. Si no se pasa `aside`, ocupa todo el ancho.
 */
export default function PageLayout({ title, subtitle, actions, aside, children, className = '' }) {
  const pageClass = ['bbva-page', !aside ? 'bbva-page--full' : '', className].filter(Boolean).join(' ')
  return (
    <div className={pageClass}>
      <div className="bbva-page-main">
        {(title || actions) && (
          <div className="bbva-page-head">
            <div>
              {title && <h1 className="bbva-page-title">{title}</h1>}
              {subtitle && <p className="bbva-page-sub">{subtitle}</p>}
            </div>
            {actions && <div className="bbva-page-actions">{actions}</div>}
          </div>
        )}
        {children}
      </div>
      {aside && <aside className="bbva-page-aside">{aside}</aside>}
    </div>
  )
}
