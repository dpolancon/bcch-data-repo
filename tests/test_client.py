import pytest
import responses
import pandas as pd
from datetime import date
from lib.client import BCChAPIClient, BCChAPIError

@responses.activate
def test_get_series_success():
    client = BCChAPIClient(user="test@example.com", password="password123")
    
    # Mock successful response
    mock_url = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
    mock_response = {
        "Series": {
            "seriesId": "F073.TCN.USD.N.O.D",
            "Obs": [
                {"indexDateString": "2026-07-01", "value": "930.5", "statusCode": "OK"},
                {"indexDateString": "2026-07-02", "value": "931.2", "statusCode": "OK"}
            ]
        }
    }
    
    responses.add(
        responses.GET,
        mock_url,
        json=mock_response,
        status=200
    )
    
    df = client.get_series(["F073.TCN.USD.N.O.D"], firstdate=date(2026, 7, 1), lastdate=date(2026, 7, 2))
    
    assert not df.empty
    assert len(df) == 2
    assert list(df.columns) == ["seriesId", "date", "value", "status"]
    assert df.iloc[0]["value"] == 930.5
    assert df.iloc[0]["date"] == pd.Timestamp("2026-07-01")

@responses.activate
def test_get_series_api_error():
    client = BCChAPIClient(user="test@example.com", password="password123")
    
    # Mock error response envelope
    mock_url = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
    mock_response = {
        "Codigo": 100,
        "Descripcion": "Invalid credentials or unauthorized series access"
    }
    
    responses.add(
        responses.GET,
        mock_url,
        json=mock_response,
        status=200
    )
    
    with pytest.raises(BCChAPIError) as excinfo:
        client.get_series(["F073.TCN.USD.N.O.D"])
        
    assert "error code 100" in str(excinfo.value)
