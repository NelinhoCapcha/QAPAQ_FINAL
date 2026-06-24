import qapaqLogo from '../../assets/images/logo_qapaq_nav-DT1cIBnc.png'

export default function Logo({ size = 44, wordmark = true, variant = 'dark' }) {
  const filter = variant === 'light' ? 'brightness(0)' : 'none'

  return (
    <span className="brand-logo" aria-label="QAPAQ" role="img">
      {wordmark ? (
        <img src={qapaqLogo} alt="QAPAQ" style={{ height: size, filter }} />
      ) : (
        <span className="brand-logo__mark" style={{ width: size, height: size, filter }}>
          Q
        </span>
      )}
    </span>
  )
}
