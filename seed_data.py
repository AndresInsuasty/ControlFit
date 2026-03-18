"""
Script temporal para poblar Google Sheets con datos de prueba.
Ejecutar una sola vez: uv run python seed_data.py
Borrar el archivo después.
"""
import sys
import uuid
import tomllib

try:
    import gspread
except ImportError:
    print("ERROR: gspread no disponible. Corre: uv sync")
    sys.exit(1)

COLUMNS = ["id", "nombre", "telefono", "fecha_inicio", "fecha_fin",
           "valor_pagado", "notas", "fecha_registro"]

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomllib.load(f)

client = gspread.service_account_from_dict(dict(secrets["gcp_service_account"]))
ws = client.open_by_url(secrets["sheet_url"]).sheet1

# ──────────────────────────────────────────────────────────────────────────────
# Datos de prueba — hoy = 17/03/2026
#
# Distribución por estado del último plan de cada alumno:
#   ACTIVO     (8): Carlos, Alejandra, Laura, Valentina, Camila, Daniela, Natalia, Isabella
#   POR VENCER (3): Andrés (vence 20/03), Diego (21/03), Mateo (22/03)
#   VENCIDO    (4): Sebastián (desertó), Juan (desertó), Felipe (no renovó), Santiago
#
# formato: (nombre, telefono, fecha_inicio, fecha_fin, valor_pagado, notas, fecha_registro)
# ──────────────────────────────────────────────────────────────────────────────
DATA = [
    # Carlos Giraldo ─ recurrente, ACTIVO
    ("Carlos Giraldo",      "3001112233", "18/12/2025", "17/01/2026", 250000, "Hipertrofia y volumen",           "2025-12-18"),
    ("Carlos Giraldo",      "3001112233", "18/01/2026", "17/02/2026", 250000, "Hipertrofia y volumen",           "2026-01-18"),
    ("Carlos Giraldo",      "3001112233", "03/03/2026", "02/04/2026", 250000, "Hipertrofia y volumen",           "2026-03-03"),

    # Alejandra Restrepo ─ recurrente, ACTIVO (renovó hoy)
    ("Alejandra Restrepo",  "3102223344", "15/12/2025", "14/01/2026", 260000, "Pérdida de peso",                "2025-12-15"),
    ("Alejandra Restrepo",  "3102223344", "15/01/2026", "14/02/2026", 260000, "Pérdida de peso",                "2026-01-15"),
    ("Alejandra Restrepo",  "3102223344", "16/02/2026", "16/03/2026", 260000, "Pérdida de peso",                "2026-02-16"),
    ("Alejandra Restrepo",  "3102223344", "17/03/2026", "16/04/2026", 260000, "Pérdida de peso",                "2026-03-17"),

    # Andrés Ospina ─ POR VENCER (vence 20/03, 3 días)
    ("Andrés Ospina",       "3153334455", "20/01/2026", "19/02/2026", 250000, "Resistencia cardiovascular",     "2026-01-20"),
    ("Andrés Ospina",       "3153334455", "20/02/2026", "20/03/2026", 250000, "Resistencia cardiovascular",     "2026-02-20"),

    # Laura Sánchez ─ recurrente, ACTIVO
    ("Laura Sánchez",       "3004445566", "28/12/2025", "27/01/2026", 270000, "Tonificación general",           "2025-12-28"),
    ("Laura Sánchez",       "3004445566", "28/01/2026", "27/02/2026", 270000, "Tonificación general",           "2026-01-28"),
    ("Laura Sánchez",       "3004445566", "28/02/2026", "28/03/2026", 270000, "Tonificación general",           "2026-02-28"),

    # Diego Cano ─ POR VENCER (vence 21/03, 4 días)
    ("Diego Cano",          "3175556677", "22/01/2026", "21/02/2026", 250000, "Entrenamiento funcional",        "2026-01-22"),
    ("Diego Cano",          "3175556677", "22/02/2026", "21/03/2026", 250000, "Entrenamiento funcional",        "2026-02-22"),

    # Valentina Londoño ─ recurrente, ACTIVO (renovó 11/03)
    ("Valentina Londoño",   "3116667788", "10/12/2025", "09/01/2026", 260000, "Yoga y fuerza",                  "2025-12-10"),
    ("Valentina Londoño",   "3116667788", "10/01/2026", "09/02/2026", 260000, "Yoga y fuerza",                  "2026-01-10"),
    ("Valentina Londoño",   "3116667788", "10/02/2026", "11/03/2026", 260000, "Yoga y fuerza",                  "2026-02-10"),
    ("Valentina Londoño",   "3116667788", "11/03/2026", "10/04/2026", 260000, "Yoga y fuerza",                  "2026-03-11"),

    # Sebastián Arango ─ desertó (1 solo plan, VENCIDO)
    ("Sebastián Arango",    "3207778899", "20/12/2025", "19/01/2026", 250000, "Cardio y quema de grasa",        "2025-12-20"),

    # Camila Betancur ─ recurrente, ACTIVO
    ("Camila Betancur",     "3148889900", "02/01/2026", "01/02/2026", 255000, "CrossFit adaptado",              "2026-01-02"),
    ("Camila Betancur",     "3148889900", "02/02/2026", "01/03/2026", 255000, "CrossFit adaptado",              "2026-02-02"),
    ("Camila Betancur",     "3148889900", "02/03/2026", "01/04/2026", 255000, "CrossFit adaptado",              "2026-03-02"),

    # Juan Tobón ─ desertó (no renovó desde febrero, VENCIDO)
    ("Juan Tobón",          "3019990011", "10/12/2025", "09/01/2026", 250000, "Fuerza y potencia",              "2025-12-10"),
    ("Juan Tobón",          "3019990011", "10/01/2026", "09/02/2026", 250000, "Fuerza y potencia",              "2026-01-10"),

    # Daniela Vargas ─ recurrente, ACTIVO
    ("Daniela Vargas",      "3170001122", "01/01/2026", "31/01/2026", 260000, "Pilates y core",                 "2026-01-01"),
    ("Daniela Vargas",      "3170001122", "01/02/2026", "02/03/2026", 260000, "Pilates y core",                 "2026-02-01"),
    ("Daniela Vargas",      "3170001122", "03/03/2026", "30/03/2026", 260000, "Pilates y core",                 "2026-03-03"),

    # Felipe Zapata ─ VENCIDO, no renovó (plan venció 05/03)
    ("Felipe Zapata",       "3121112233", "05/01/2026", "04/02/2026", 250000, "HIIT y quema calórica",          "2026-01-05"),
    ("Felipe Zapata",       "3121112233", "05/02/2026", "05/03/2026", 250000, "HIIT y quema calórica",          "2026-02-05"),

    # Natalia Ríos ─ alumna nueva, ACTIVO
    ("Natalia Ríos",        "3132223344", "10/03/2026", "09/04/2026", 250000, "Iniciación al gym",              "2026-03-10"),

    # Santiago Montoya ─ VENCIDO (venció 10/03, hace 7 días)
    ("Santiago Montoya",    "3183334455", "10/12/2025", "09/01/2026", 265000, "Musculación avanzada",           "2025-12-10"),
    ("Santiago Montoya",    "3183334455", "10/01/2026", "09/02/2026", 265000, "Musculación avanzada",           "2026-01-10"),
    ("Santiago Montoya",    "3183334455", "10/02/2026", "10/03/2026", 265000, "Musculación avanzada",           "2026-02-10"),

    # Isabella Henao ─ alumna nueva, ACTIVO
    ("Isabella Henao",      "3054445566", "12/03/2026", "11/04/2026", 250000, "Acondicionamiento físico",       "2026-03-12"),

    # Mateo Muñoz ─ POR VENCER (vence 22/03, 5 días) — paga un poco más (personal)
    ("Mateo Muñoz",         "3165556677", "23/01/2026", "22/02/2026", 300000, "Powerlifting y fuerza máxima",   "2026-01-23"),
    ("Mateo Muñoz",         "3165556677", "23/02/2026", "22/03/2026", 300000, "Powerlifting y fuerza máxima",   "2026-02-23"),
]

rows = [
    [str(uuid.uuid4()), nombre, telefono, fi, ff, valor, notas, f"{reg}T08:00:00-05:00"]
    for nombre, telefono, fi, ff, valor, notas, reg in DATA
]

print("Limpiando sheet...")
ws.clear()

print("Insertando encabezado...")
ws.append_row(COLUMNS)

print(f"Insertando {len(rows)} registros...")
ws.append_rows(rows, value_input_option="USER_ENTERED")

print(f"\n✅ Listo. {len(rows)} registros insertados.")
print("\nDistribución esperada:")
print("  ACTIVO     (8): Carlos, Alejandra, Laura, Valentina, Camila, Daniela, Natalia, Isabella")
print("  POR VENCER (3): Andrés (20/03), Diego (21/03), Mateo (22/03)")
print("  VENCIDO    (4): Sebastián, Juan, Felipe, Santiago")
