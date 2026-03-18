import pandas as pd
import streamlit as st
import gspread

COLUMNS = ["id", "nombre", "telefono", "fecha_inicio", "fecha_fin",
           "valor_pagado", "notas", "fecha_registro"]


def _get_worksheet():
    """Return the first worksheet of the configured Google Sheet."""
    client = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    sheet = client.open_by_url(st.secrets["sheet_url"])
    return sheet.sheet1


def get_data() -> pd.DataFrame:
    """Read all rows from Google Sheet. Returns empty DataFrame on error."""
    empty = pd.DataFrame(columns=COLUMNS)
    try:
        ws = _get_worksheet()
        records = ws.get_all_records()
        if not records:
            return empty
        df = pd.DataFrame(records)
        df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"], format="%d/%m/%Y", dayfirst=True)
        df["fecha_fin"] = pd.to_datetime(df["fecha_fin"], format="%d/%m/%Y", dayfirst=True)
        df["valor_pagado"] = pd.to_numeric(df["valor_pagado"], errors="coerce").fillna(0.0)
        df["fecha_registro"] = pd.to_datetime(df["fecha_registro"], format="ISO8601", utc=True).dt.tz_convert("America/Bogota")
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return empty


def append_record(record: dict) -> None:
    """Append a new row to the sheet."""
    try:
        ws = _get_worksheet()
        row = [record.get(col, "") for col in COLUMNS]
        ws.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        st.error(f"Error al guardar el registro: {e}")


def update_record(record_id: str, record: dict) -> None:
    """Find row by id and update all fields."""
    try:
        ws = _get_worksheet()
        cell = ws.find(record_id, in_column=1)
        if cell is None:
            st.error("Registro no encontrado. Puede haber sido eliminado de Google Sheets.")
            return
        row_values = [record.get(col, "") for col in COLUMNS]
        ws.update(f"A{cell.row}", [row_values])
    except Exception as e:
        st.error(f"Error al actualizar el registro: {e}")
