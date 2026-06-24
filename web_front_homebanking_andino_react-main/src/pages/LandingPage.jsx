import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BadgePercent,
  ChevronLeft,
  ChevronRight,
  Landmark,
  MapPin,
  PiggyBank,
  ShieldCheck,
  Smartphone,
  WalletCards,
} from 'lucide-react'
import PublicHeader from '../components/layout/PublicHeader.jsx'
import PublicFooter from '../components/layout/PublicFooter.jsx'
import bannerDeposito from '../assets/images/banner-body-pc-deposito-plazo.png'
import bannerFraudes from '../assets/images/banner-body-pc-fraudes.png'
import bannerVivienda from '../assets/images/banner-body-vivenda.jpg'
import slideAhorros from '../assets/images/slide-cuenta-ahorros.png'
import slideQambios from '../assets/images/slide-qambios.png'
import slideCompromiso from '../assets/images/slide-valoramos-tu-compromiso.png'

const SLIDES = [
  {
    image: slideCompromiso,
    imageName: 'slide-valoramos-tu-compromiso.png',
    eyebrow: 'Campana QAPAQ',
    title: 'Valoramos tu compromiso',
    text: 'Mantente al dia y accede a beneficios pensados para seguir creciendo.',
    cta: 'Conoce mas',
  },
  {
    image: slideAhorros,
    imageName: 'slide-cuenta-ahorros.png',
    eyebrow: 'Ahorros',
    title: 'Cuenta Ahorros Insuperable',
    text: 'Haz que tus ahorros avancen con una cuenta simple, cercana y segura.',
    cta: 'Abre tu cuenta',
  },
  {
    image: slideQambios,
    imageName: 'slide-qambios.png',
    eyebrow: 'Qapaq Qambios',
    title: 'Cambia dolares desde donde estes',
    text: 'Consulta el tipo de cambio y opera desde tus canales digitales.',
    cta: 'Ver beneficios',
  },
]

const SHORTCUTS = [
  { label: 'Qapaq por INTERNET', type: 'dark', route: '/login' },
  { label: 'Abre tu CUENTA', type: 'yellow', route: '/login' },
  { label: 'Solicita tu PRESTAMO', type: 'red', route: '/login' },
]

const PRODUCTOS = [
  { icon: Landmark, title: 'Para tu negocio', text: 'Creditos para mercaderia, maquinaria, cultivo y capital de trabajo.' },
  { icon: BadgePercent, title: 'Para ti', text: 'Prestamos de consumo, efectivo rapido y soluciones con garantia.' },
  { icon: PiggyBank, title: 'Ahorros', text: 'Cuentas de ahorro, plazo fijo, CTS y alternativas para hacer crecer tu dinero.' },
  { icon: Smartphone, title: 'Canales digitales', text: 'Opera desde Qapaq por Internet y desde la app movil cuando lo necesites.' },
]

const BANNERS = [
  {
    image: bannerVivienda,
    name: 'banner-body-vivenda.jpg',
    title: 'Vivienda para tu familia',
  },
  {
    image: bannerDeposito,
    name: 'banner-body-pc-deposito-plazo.png',
    title: 'Ahorra con confianza',
  },
  {
    image: bannerFraudes,
    name: 'banner-body-pc-fraudes.png',
    title: 'Protege tus operaciones',
  },
]

export default function LandingPage() {
  const navigate = useNavigate()
  const [active, setActive] = useState(0)
  const slide = SLIDES[active]

  const dots = useMemo(() => SLIDES.map((item, index) => ({ label: item.imageName, index })), [])

  const goSlide = (direction) => {
    setActive((current) => (current + direction + SLIDES.length) % SLIDES.length)
  }

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActive((current) => (current + 1) % SLIDES.length)
    }, 7000)

    return () => window.clearInterval(timer)
  }, [])

  return (
    <div className="qweb-page">
      <PublicHeader />

      <section className="qweb-shortcuts" aria-label="Accesos rapidos">
        {SHORTCUTS.map((item) => (
          <button
            key={item.label}
            className={`qweb-shortcut qweb-shortcut--${item.type}`}
            onClick={() => navigate(item.route)}
          >
            {item.label}
          </button>
        ))}
      </section>

      <section className="qweb-slider" aria-label="Promociones principales">
        <button className="qweb-slider__arrow qweb-slider__arrow--left" onClick={() => goSlide(-1)} aria-label="Anterior">
          <ChevronLeft size={28} />
        </button>

        <button className="qweb-slide" onClick={() => navigate('/login')} aria-label={`Ir a HomeBanking: ${slide.title}`}>
          <div className="qweb-slide__image">
            <img src={slide.image} alt={slide.title} />
          </div>
        </button>

        <button className="qweb-slider__arrow qweb-slider__arrow--right" onClick={() => goSlide(1)} aria-label="Siguiente">
          <ChevronRight size={28} />
        </button>

        <div className="qweb-slider__dots">
          {dots.map((dot) => (
            <button
              key={dot.label}
              className={dot.index === active ? 'active' : ''}
              onClick={() => setActive(dot.index)}
              aria-label={`Ver ${dot.label}`}
            />
          ))}
        </div>
      </section>

      <section className="qweb-product-strip" aria-label="Productos principales">
        {PRODUCTOS.map((producto) => {
          const Icon = producto.icon
          return (
            <button key={producto.title} className="qweb-product-card" onClick={() => navigate('/login')}>
              <Icon size={30} />
              <strong>{producto.title}</strong>
              <span>{producto.text}</span>
            </button>
          )
        })}
      </section>

      <section className="qweb-body-banners" aria-label="Banners informativos">
        {BANNERS.map((banner) => (
          <article key={banner.name} className="qweb-info-banner">
            <img src={banner.image} alt={banner.title} />
          </article>
        ))}
      </section>

      <section className="qweb-service-band">
        <div>
          <ShieldCheck size={26} />
          <strong>Operacion segura</strong>
          <span>Canales digitales disponibles para consultar, pagar y transferir.</span>
        </div>
        <div>
          <MapPin size={26} />
          <strong>Ubicanos</strong>
          <span>Agencias y agentes recaudadores cerca de ti.</span>
        </div>
        <div>
          <WalletCards size={26} />
          <strong>Servicios</strong>
          <span>Pagos, transferencias y beneficios para clientes QAPAQ.</span>
        </div>
      </section>

      <PublicFooter />
    </div>
  )
}
