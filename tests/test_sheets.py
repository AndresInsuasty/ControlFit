import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from data.sheets import get_data, append_record, update_record, COLUMNS

SAMPLE_RECORDS = [
    {
        "id": "uuid-001",
        "nombre": "Juan Perez",
        "telefono": "3001234567",
        "fecha_inicio": "01/01/2026",
        "fecha_fin": "31/01/2026",
        "valor_pagado": 150000.0,
        "notas": "",
        "fecha_registro": "2026-01-01T10:00:00",
    }
]


def mock_worksheet(records=None):
    ws = MagicMock()
    ws.get_all_records.return_value = records if records is not None else []
    return ws


# --- get_data ---

def test_get_data_returns_dataframe():
    with patch("data.sheets._get_worksheet", return_value=mock_worksheet(SAMPLE_RECORDS)):
        df = get_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["nombre"] == "Juan Perez"

def test_get_data_parses_dates():
    with patch("data.sheets._get_worksheet", return_value=mock_worksheet(SAMPLE_RECORDS)):
        df = get_data()
    assert pd.api.types.is_datetime64_any_dtype(df["fecha_inicio"])
    assert pd.api.types.is_datetime64_any_dtype(df["fecha_fin"])

def test_get_data_parses_valor_pagado():
    with patch("data.sheets._get_worksheet", return_value=mock_worksheet(SAMPLE_RECORDS)):
        df = get_data()
    assert df["valor_pagado"].dtype == float

def test_get_data_empty_sheet_returns_empty_df():
    with patch("data.sheets._get_worksheet", return_value=mock_worksheet([])):
        df = get_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == COLUMNS

def test_get_data_on_error_returns_empty_df():
    ws = MagicMock()
    ws.get_all_records.side_effect = Exception("Network error")
    with patch("data.sheets._get_worksheet", return_value=ws):
        with patch("streamlit.error") as mock_error:
            df = get_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    mock_error.assert_called_once()


# --- append_record ---

def test_append_record_calls_append_row():
    ws = mock_worksheet()
    record = {
        "id": "uuid-new",
        "nombre": "Ana Lopez",
        "telefono": "",
        "fecha_inicio": "01/03/2026",
        "fecha_fin": "31/03/2026",
        "valor_pagado": 200000.0,
        "notas": "",
        "fecha_registro": "2026-03-01T09:00:00",
    }
    with patch("data.sheets._get_worksheet", return_value=ws):
        append_record(record)
    ws.append_row.assert_called_once()
    call_args = ws.append_row.call_args[0][0]
    assert call_args[0] == "uuid-new"
    assert call_args[1] == "Ana Lopez"


# --- update_record ---

def test_update_record_updates_correct_row():
    ws = mock_worksheet(SAMPLE_RECORDS)
    # gspread rows are 1-indexed, row 1 = header, row 2 = first data row
    ws.find.return_value = MagicMock(row=2)
    with patch("data.sheets._get_worksheet", return_value=ws):
        update_record("uuid-001", {**SAMPLE_RECORDS[0], "nombre": "Juan Actualizado"})
    ws.update.assert_called_once()

def test_update_record_not_found_shows_error():
    ws = mock_worksheet([])
    ws.find.side_effect = Exception("Not found")
    with patch("data.sheets._get_worksheet", return_value=ws):
        with patch("streamlit.error") as mock_error:
            update_record("nonexistent-id", {})
    mock_error.assert_called_once()
