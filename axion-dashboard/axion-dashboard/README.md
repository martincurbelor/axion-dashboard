# Axion Energy — Dashboard de Ventas

Dashboard web con datos desde MySQL local, publicado en GitHub Pages.

---

## Estructura del proyecto

```
axion-dashboard/
├── index.html              ← El dashboard (no tocar)
├── datos.json              ← Generado automáticamente por el script
├── procesar_datos.py       ← Script principal: lee MySQL y sube a GitHub
├── ejecutar.bat            ← El Programador de tareas llama a este archivo
├── requirements.txt        ← Dependencias Python
└── .github/
    └── workflows/
        └── actualizar.yml  ← Ya no se usa con MySQL local (podés borrar)
```

---

## Configuración inicial (una sola vez)

### Paso 1 — Instalar dependencias Python

Abrí una terminal (cmd o PowerShell) y ejecutá:

```bat
pip install mysql-connector-python pandas
```

### Paso 2 — Configurar la conexión a MySQL

Abrí `procesar_datos.py` con cualquier editor (Notepad, VS Code, etc.)
y editá las primeras líneas:

```python
DB = {
    'host':     'localhost',
    'port':     3306,
    'user':     'root',
    'password': 'tu_password',   # <-- tu contraseña de MySQL
    'database': 'tu_base',       # <-- nombre de tu base de datos
}

TABLA = 'ventas'   # nombre de la tabla
```

### Paso 3 — Configurar Git y GitHub

1. Instalá Git para Windows: https://git-scm.com/download/win
2. Creá un repositorio privado en GitHub llamado `axion-dashboard`
3. En la carpeta del proyecto, abrí una terminal y ejecutá:

```bat
git init
git add .
git commit -m "primer commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/axion-dashboard.git
git push -u origin main
```

4. La primera vez que hagas push, Windows te va a pedir que inicies sesión
   en GitHub. Hacelo con tu usuario y contraseña (o token).

### Paso 4 — Activar GitHub Pages

1. En tu repositorio de GitHub: **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / carpeta: **/ (root)**
4. Click **Save**
5. En ~2 minutos tenés tu URL: `https://TU_USUARIO.github.io/axion-dashboard`

### Paso 5 — Probar que todo funciona

Ejecutá el script manualmente la primera vez:

```bat
ejecutar.bat
```

Deberías ver algo así:

```
Conectando a MySQL...
Leyendo datos...
  39.097 registros leídos
✓ datos.json generado — {'2026': ['2']}
Subiendo a GitHub...
  ✓ GitHub actualizado
✓ Proceso completado
```

---

## Automatización con el Programador de tareas de Windows

Para que el script corra solo todos los días:

1. Abrí el **Programador de tareas** (buscalo en el menú Inicio)
2. Click en **Crear tarea básica...**
3. **Nombre:** `Axion Dashboard - Actualizar datos`
4. **Desencadenador:** Diariamente
5. **Hora:** 06:00 AM (o la que prefieras)
6. **Acción:** Iniciar un programa
7. **Programa:** buscá y seleccioná `ejecutar.bat` en la carpeta del proyecto
8. **Iniciar en:** la carpeta del proyecto (ej: `C:\axion-dashboard`)
9. Finalizá y guardá

> ⚠️ La PC tiene que estar encendida a la hora programada.
> Si se apagó, la tarea no corre hasta el día siguiente.

---

## Verificar que el dashboard se actualizó

Después de que corre el script:
1. Entrá a tu repositorio en GitHub
2. Revisá que `datos.json` tenga fecha de hoy en el último commit
3. Abrí el dashboard — en el header dice "actualizado YYYY-MM-DD"

---

## Solución de problemas

**"No module named mysql.connector"**
```bat
pip install mysql-connector-python
```

**"Access denied for user 'root'"**
→ Revisá usuario y contraseña en `procesar_datos.py`

**"git no se reconoce como comando"**
→ Instalá Git para Windows: https://git-scm.com/download/win
→ Cerrá y volvé a abrir la terminal después de instalarlo

**El script corre pero el dashboard no cambia**
→ Fijate si el archivo `datos.json` cambió en GitHub
→ Probá forzar recarga en el browser con Ctrl+Shift+R

---

## Contacto técnico

Pento Analytics · Montevideo, Uruguay
