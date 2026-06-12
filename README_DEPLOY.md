# Polla Mundial 2026 — App web

App en Streamlit para que los 25 participantes apuesten desde el celular.
Login por PIN, bloqueo por hora de cada partido, contador al próximo partido,
ranking en vivo y panel de administrador.

## Probar en tu PC (local, sin nube)

```
cd "C:\Users\CO1015470664\Polla Web"
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Se abre en el navegador (http://localhost:8501). Usa SQLite local (`polla.db`).
Para cargar las apuestas/claves actuales del Excel:  `py migrar_excel.py`

## Publicar gratis para que entren desde el celular

Necesitas 2 cuentas gratis (una vez). Te guío:

### 1) Base de datos — Supabase (gratis)
1. Entra a https://supabase.com → *Start your project* (inicia con GitHub o Google).
2. *New project* → ponle nombre (ej. `polla`) y una contraseña de base (guárdala).
3. Espera ~2 min a que cree el proyecto.
4. Ve a *Project Settings → Database → Connection string → URI*.
   Copia algo como `postgresql://postgres:CONTRASEÑA@db.xxxx.supabase.co:5432/postgres`.

### 2) Hosting — Streamlit Community Cloud (gratis)
1. Sube esta carpeta a un repositorio de GitHub (te ayudo con los comandos).
2. Entra a https://share.streamlit.io → inicia con GitHub.
3. *New app* → elige tu repo, branch `main`, archivo `app.py` → *Deploy*.
4. En *Advanced settings → Secrets*, pega:
   ```
   DATABASE_URL = "postgresql://postgres:CONTRASEÑA@db.xxxx.supabase.co:5432/postgres"
   PIN_SALT = "algo-tuyo-secreto"
   ADMINS = "Federico Franco"
   ```
5. *Deploy*. En 1-2 min tendrás un link público tipo `https://tu-polla.streamlit.app`.

### 3) Migrar las apuestas actuales a la nube
Con la `DATABASE_URL` de Supabase puesta como variable de entorno, corre
`py migrar_excel.py` una vez (lee los 25 Excel y las sube a la base).

### 4) Comparte el link
Pasas el link al grupo de WhatsApp. Cada quien entra, elige su nombre,
crea su PIN y apuesta. ¡Todos a la vez, desde el celular!

## Notas
- El admin (Federico) ve la pestaña **Admin** para cargar resultados y resetear PINs.
- El bloqueo por hora usa la hora del servidor (Colombia). Tras el pitazo, el partido
  queda de solo lectura.
- El Excel sigue intacto como respaldo hasta que decidas migrar del todo.
