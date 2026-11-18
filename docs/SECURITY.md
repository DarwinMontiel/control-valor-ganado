# Seguridad

## Alcance

Es una herramienta interna de demostración **sin autenticación ni multiusuario**. Decidí no agregar un login a medias: una autenticación ficticia da una falsa sensación de seguridad. Antes de exponerla fuera de una red de confianza hay que agregar autenticación (por ejemplo, OIDC con el proveedor de la empresa) y autorización por proyecto.

## Medidas aplicadas

| Riesgo | Medida |
|--------|--------|
| Inyección SQL | Solo consultas del ORM con parámetros. La búsqueda por nombre usa `ilike` con un parámetro, no concatenación |
| Datos inválidos | Validación en tres niveles: Pydantic (contrato HTTP), dominio (`ActivityProgress`) y `CHECK` en PostgreSQL |
| Fuga de detalles internos | Un formato de error único: los 404 y 422 no exponen trazas ni SQL |
| Peticiones abusivas | `limit` máximo de 100 en la paginación; nginx limita el cuerpo a 64 KB; los textos tienen longitud máxima |
| CORS | En Docker, la web y la API comparten origen detrás de nginx. En desarrollo, solo `localhost:5173` y solo los métodos y cabeceras necesarios |
| Secretos | Nada en el repositorio: la configuración viene de variables de entorno (`.env.example` solo tiene valores locales) |
| Contenedores | La API corre con un usuario sin privilegios (uid 10001) |
| Cabeceras | `X-Content-Type-Options: nosniff`, `Referrer-Policy` y `server_tokens off` en nginx |
| Borrados accidentales | La interfaz pide confirmación y dice qué se borrará, incluidas las actividades del proyecto |
| Dependencias | Versiones fijadas en `pyproject.toml` y `package-lock.json`; permisos de solo lectura en GitHub Actions |
