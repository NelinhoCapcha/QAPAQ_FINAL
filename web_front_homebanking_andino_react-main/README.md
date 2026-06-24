# Banco Andino â€” Banca por Internet (Homebanking)

Portal del **cliente final** de Banco Andino, construido en **React 18 + Vite (JavaScript)**.
Consume el backend FastAPI del Homebanking que corre en `http://localhost:8002`.

> Identidad visual de **Banco Andino**: isotipo de flor andina multicolor, paleta del textil
> andino (rojo `#e2132b`, magenta, turquesa, naranja, moradoâ€¦), **franja tejida** superior,
> header con gradiente de marca, menÃº horizontal de Ã­conos circulares y tarjetas redondeadas.

---

## Requisitos

- Node.js 18+ (probado con Node 24)
- El backend FastAPI del Homebanking corriendo en `http://localhost:8002`
  (el portal del **personal** usa el puerto `5173`; este portal del **cliente** usa el `5174`).

## Puesta en marcha

```bash
npm install
npm run dev
```

La app queda disponible en **http://localhost:5174**.

### Variable de entorno

Copie `.env.example` a `.env` y ajuste si su backend no estÃ¡ en el puerto por defecto:

```
VITE_BASE_URL=http://localhost:8002
```

## Acceso de prueba

El ingreso solicita usuario, DNI y clave de internet.

> Por seguridad, las credenciales de prueba no se publican en este README; deben entregarse por un canal interno del entorno.

---

## Estructura del proyecto

```
src/
  services/      hb_api.js (axios central con interceptores) + un service por dominio
                 (authService, cuentasService, operacionesService, creditosService)
  context/       HBAuthContext.jsx           (estado de sesiÃ³n)
  hooks/         useHBAuth, useCuentas, useMovimientos, useCreditos, useOperaciones
  components/
    layout/      PublicHeader + PublicFooter (sitio pÃºblico), Header (menÃº de Ã­conos
                 de la banca), PrivateRoute
    ui/          Logo (flor andina), Card, Tabla, Loader, Badge, Money, Alert
  pages/         LandingPage (home marketero), LoginPage, HomePage, CuentasAhorroPage,
                 MovimientosPage, CuentasCreditoPage, CuotasCreditoPage, PagoCuotaPage,
                 TransferenciaPage, SolicitarCreditoPage
  utils/         format.js  (S/ 1,234.56, fechas dd/mm/yyyy, parseo de errores)
  App.jsx Â· main.jsx Â· index.css
```

## AutenticaciÃ³n

- `POST /auth/login {username, dni, password}` â†’ `{ access_token, cliente: { codcliente, nombre, ... } }`.
- El token se guarda en `localStorage` bajo la clave **`hb_token`** y los datos del cliente en **`hb_user`**.
- La instancia central de axios (`services/hb_api.js`):
  - inyecta `Authorization: Bearer <token>` en cada request,
  - ante un **401** limpia la sesiÃ³n y redirige a `/login`.
- Las rutas privadas (`PrivateRoute`) redirigen a `/login` si no hay token.

## Flujo de navegaciÃ³n

```
/  (pÃºblico)  Home marketero  â”€â”€â–º  /login  â”€â”€â–º  /inicio  (banca privada)
```

- La raÃ­z `/` es un **home marketero pÃºblico** (estilo banca peruana): hero, productos,
  beneficios, promo y footer. Incluye un **widget "Banca por Internet"** donde el cliente
  escribe su **NÂ° de tarjeta de ahorros** y continÃºa al login (que viaja precargado).
- `/login` pide la **clave de Internet** y autentica contra el backend.
- Tras iniciar sesiÃ³n se entra a `/inicio` y al resto de la banca privada.

## Pantallas

0. **Home marketero** (`/`, pÃºblico) â€” hero con gradiente de marca, accesos rÃ¡pidos, grilla de
   productos (Ahorros, Cuenta Sueldo, CrÃ©ditos, Tarjetasâ€¦), beneficios, promo y footer. CTA
   "Banca por Internet" e ingreso con nÃºmero de tarjeta de ahorros.
1. **Login** â€” tarjeta centrada con logo Banco Andino sobre el gradiente de marca y franja tejida.
2. **Inicio** (`/inicio`) â€” bienvenida personalizada + accesos rÃ¡pidos.
3. **Consultas â€º Cuentas de Ahorro** â€” tabla separada por Soles/DÃ³lares, con Movimientos y Detalle.
4. **Movimientos** â€” cabecera de la cuenta (producto, nÂ°, saldo, TEA) + tabla de movimientos.
5. **Consultas â€º Cuentas de CrÃ©dito** â€” saldo capital, pago pendiente, calificaciÃ³n, ver cuotas.
6. **Cronograma de cuotas** â€” nÂ° cuota, vencimiento, monto, dÃ­as de mora; botÃ³n "Pagar prÃ³xima cuota".
7. **Operaciones â€º Pago Cuotas CrÃ©ditos** â€” confirma el pago y muestra comprobante.
8. **Operaciones â€º Transferencias Propias** â€” origen/destino entre cuentas del cliente + comprobante.
9. **CrÃ©ditos â€º Producto Digital** â€” formulario de solicitud; maneja el **422 de elegibilidad**
   (cliente no apto) mostrando el motivo de forma amable.

## Endpoints consumidos

| MÃ©todo | Endpoint | Uso |
|--------|----------|-----|
| POST | `/auth/login` | Login del cliente |
| GET  | `/cuentas/ahorro` | Cuentas de ahorro |
| GET  | `/cuentas/ahorro/{cod}/movimientos?limit=50` | Movimientos |
| GET  | `/cuentas/credito` | CrÃ©ditos |
| GET  | `/cuentas/credito/{cod}/cuotas` | Cronograma |
| POST | `/operaciones/pago-cuota` | Pago de cuota |
| POST | `/operaciones/transferencia` | Transferencia propia |
| POST | `/creditos/solicitar` | Solicitud de crÃ©dito (ME/CO) |

## Manejo de errores / UX

- Loader mientras carga cada vista; mensaje claro si un endpoint falla.
- Montos formateados como `S/ 1,234.56`; fechas como `dd/mm/yyyy`.
- Tras pagar/transferir/solicitar, la vista correspondiente se refresca.
- Errores del backend (`{detail: "..."}`, validaciÃ³n 422, o `{detail:{error, elegibilidad}}`)
  se traducen a mensajes amables (ver `utils/format.js â†’ extractError`).

## Build de producciÃ³n

```bash
npm run build
npm run preview
```

