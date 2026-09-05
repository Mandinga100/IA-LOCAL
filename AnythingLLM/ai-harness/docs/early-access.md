# Early Access y Gestión de Usuarios — Asistente Integral 360

Este documento describe el flujo de captura de leads por early access.

---

## 1. Flujo de Early Access

```
Usuario ingresa email en formulario
  → Validación cliente (React Hook Form + Zod)
  → Server Action (subscribeToEarlyAccess)
  → Validación servidor (Zod)
  → Simulación: console.warn + setTimeout (ACTUAL)
  → Backend real: Firebase/Email API (PENDIENTE)
  → Mensaje de confirmación al usuario
```

## 2. Estado Actual

| Componente | Estado |
|:-----------|:-------|
| `early-access-form.tsx` | Cliente: validación Zod, estados loading/success/error, toast |
| `early-access-section.tsx` | Server: layout de dos columnas con beneficios y form |
| `actions.ts` | Server Action: validación Zod + simulación (`console.warn`) |

## 3. Pendiente de Implementación

- [ ] Conectar a Firebase Firestore (colección `subscriptions`)
- [ ] O Firebase Data Connect (PostgreSQL)
- [ ] O servicio de email (SendGrid, Resend, etc.)
- [ ] Verificación de email único
- [ ] Rate limiting / anti-spam
- [ ] Notificación al equipo cuando alguien se suscribe

## 4. Reglas de Privacidad de Datos

- Los emails recolectados solo se usarán para notificaciones de early access
- No compartir con terceros
- Opción de darse de baja en cada comunicación
- Cumplimiento GDPR/Ley de Protección de Datos Chile
