# DB Reset y Persistencia (PostgreSQL)

## 1) Reset completo de base de datos (solo cuando lo necesites)

Esto elimina contenedores y volumen de PostgreSQL, y vuelve a ejecutar el init SQL.

```bash
docker compose down -v
docker compose up --build
```

## 2) Levantamiento normal con persistencia

Una vez hecho el reset inicial, usa estos comandos para no perder datos:

```bash
docker compose down
docker compose up --build
```

## Nota

- El backend ya está configurado para usar solo PostgreSQL.
- El script de init `src/db/postgres/init/01_schema_and_seed.sql` solo se ejecuta cuando la data del volumen es nueva.
