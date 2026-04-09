# Credenciales de Desarrollo

Este archivo es solo para entorno local de desarrollo.

## Login de la aplicacion (API/Frontend)

- Admin
  - Correo: `admin@pqr.com`
  - Contrasena: `admin123`
  - Rol: `admin`

- Supervisor
  - Correo: `laura@pqr.com`
  - Contrasena: `super456`
  - Rol: `supervisor`

- Agente
  - Correo: `carlos@pqr.com`
  - Contrasena: `agente789`
  - Rol: `agente`

- Usuario
  - Correo: `maria@pqr.com`
  - Contrasena: `user000`
  - Rol: `usuario`

- Usuario inactivo (referencia de pruebas)
  - Correo: `pedro@pqr.com`
  - Contrasena: `inact111`
  - Rol: `usuario`
  - Estado: `inactivo`

## Adminer / PostgreSQL

- URL: `http://localhost:8080`
- System: `PostgreSQL`
- Server: `postgres`
- Username: `pqr_user`
- Password: `pqr_password`
- Database: `pqr_db`

## Nota tecnica

- Las contrasenas de usuarios se almacenan hasheadas en base de datos.
- Las contrasenas listadas aqui son las de acceso en texto claro para desarrollo local.
- Registro habilitado en: `POST /auth/register` y pantalla `http://localhost:5173/register`.
