# ControlFit 💪

La forma más simple de controlar alumnos de entrenamiento personal.

Digitaliza tu libreta: ve quién está activo, quién renueva pronto y cuánto ingresó este mes.

---

## Requisitos previos

- Python 3.11+
- Cuenta de Google
- Acceso a [Google Cloud Console](https://console.cloud.google.com/)

---

## 1. Crear la hoja de Google Sheets

1. Crea una nueva hoja en [Google Sheets](https://sheets.google.com)
2. En la primera fila, agrega exactamente estos encabezados (respeta mayúsculas y guiones bajos):

```
id | nombre | telefono | fecha_inicio | fecha_fin | valor_pagado | notas | fecha_registro
```

3. Copia la URL de la hoja (la necesitarás más adelante)

---

## 2. Configurar credenciales de Google

### 2a. Crear proyecto y habilitar APIs

1. Ve a [Google Cloud Console](https://console.cloud.google.com/) → Nuevo proyecto
2. En el menú, ve a **APIs y Servicios → Biblioteca**
3. Busca y habilita: **Google Sheets API** y **Google Drive API**

### 2b. Crear cuenta de servicio

1. Ve a **APIs y Servicios → Credenciales → Crear credenciales → Cuenta de servicio**
2. Dale un nombre, haz clic en Crear
3. En la cuenta creada, ve a la pestaña **Claves → Agregar clave → JSON**
4. Descarga el archivo JSON — guárdalo de forma segura

### 2c. Compartir la hoja con la cuenta de servicio

1. Abre el JSON descargado y copia el valor de `client_email` (termina en `.iam.gserviceaccount.com`)
2. Ve a tu Google Sheet → Compartir → pega ese email → rol **Editor** → Listo

---

## 3. Configurar secrets locales

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edita `.streamlit/secrets.toml` y completa:

- `password`: la contraseña que usarás para entrar a la app
- `sheet_url`: la URL de tu Google Sheet
- `[gcp_service_account]`: copia **todos** los campos del JSON descargado como claves TOML

---

## 4. Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre `http://localhost:8501` e ingresa la contraseña configurada.

---

## 5. Desplegar en Streamlit Community Cloud

1. Sube el proyecto a GitHub (asegúrate de que `.streamlit/secrets.toml` esté en `.gitignore`)
2. Ve a [share.streamlit.io](https://share.streamlit.io) → New app
3. Selecciona tu repositorio y `app.py` como archivo principal
4. Ve a **Advanced settings → Secrets** y pega el contenido de tu `secrets.toml`
5. Haz clic en Deploy

---

## Estructura del proyecto

```
controlfit/
├── app.py                  ← Login y punto de entrada
├── pages/
│   ├── 1_Dashboard.py      ← Métricas e ingresos
│   ├── 2_Alumnos.py        ← Tabla con estados
│   └── 3_Gestion.py        ← Agregar y editar alumnos
├── data/
│   ├── sheets.py           ← Conexión con Google Sheets
│   └── calculations.py     ← Lógica de estados y métricas
├── tests/                  ← Tests unitarios
└── requirements.txt
```

---

## Nota sobre eliminar registros

En esta versión MVP, los registros se eliminan directamente en Google Sheets. Simplemente borra la fila correspondiente.
