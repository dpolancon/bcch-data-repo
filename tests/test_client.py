"""
Purpose:  Tests for the BCCh API client -- response parsing, error envelopes,
          the two auth schemes, and day-first date handling.
Task:     BCCh data pipeline infrastructure
Inputs:   n/a (HTTP mocked with `responses`)
Outputs:  n/a
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon

Fixtures below use the API's real date format, DD-MM-YYYY. An earlier version
of this file used ISO strings, which the API never sends; that fixture passed
only because the client parsed dates without an explicit format.
"""

import pandas as pd
import pytest

responses = pytest.importorskip(
    "responses", reason="install dev extras: pip install -e .[dev]"
)

from datetime import date

from lib.client import BCChAPIClient, BCChAPIError

MOCK_URL = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"


def make_client(**kwargs):
    return BCChAPIClient(min_request_interval=0, **kwargs)


@responses.activate
def test_get_series_success():
    client = make_client(user="test@example.com", password="password123")

    responses.add(
        responses.GET,
        MOCK_URL,
        json={
            "Series": {
                "seriesId": "F073.TCN.USD.N.O.D",
                # DD-MM-YYYY, as the API actually returns.
                "Obs": [
                    {"indexDateString": "01-07-2026", "value": "930.5", "statusCode": "OK"},
                    {"indexDateString": "02-07-2026", "value": "931.2", "statusCode": "OK"},
                ],
            }
        },
        status=200,
    )

    df = client.get_series(
        ["F073.TCN.USD.N.O.D"], firstdate=date(2026, 7, 1), lastdate=date(2026, 7, 2)
    )

    assert not df.empty
    assert len(df) == 2
    assert list(df.columns) == ["seriesId", "date", "value", "status"]
    assert df.iloc[0]["value"] == 930.5
    assert df.iloc[0]["date"] == pd.Timestamp("2026-07-01")


@responses.activate
def test_dates_are_parsed_day_first():
    """`03-08-2026` is 3 August, not 8 March.

    Without an explicit format pandas reads days 1-12 as month-first while
    reading days 13-31 correctly, so only part of a series is corrupted -- the
    hardest kind of error to notice. Both cases are pinned here.
    """
    client = make_client(token="t0ken")

    responses.add(
        responses.GET,
        MOCK_URL,
        json={
            "Series": {
                "seriesId": "F073.TCO.PRE.Z.D",
                "Obs": [
                    {"indexDateString": "03-08-2026", "value": "1.0", "statusCode": "OK"},
                    {"indexDateString": "13-08-2026", "value": "2.0", "statusCode": "OK"},
                ],
            }
        },
        status=200,
    )

    df = client.get_series(["F073.TCO.PRE.Z.D"])
    assert list(df["date"]) == [pd.Timestamp("2026-08-03"), pd.Timestamp("2026-08-13")]


@responses.activate
def test_token_auth_sends_token_not_credentials():
    client = make_client(token="s3cret-token")
    responses.add(responses.GET, MOCK_URL, json={"Series": {"seriesId": "X", "Obs": []}}, status=200)

    client.get_series(["X"])

    query = responses.calls[0].request.url
    assert "token=s3cret-token" in query
    assert "pass=" not in query


@responses.activate
def test_legacy_auth_sends_user_and_pass():
    client = make_client(user="me@example.com", password="pw")
    responses.add(responses.GET, MOCK_URL, json={"Series": {"seriesId": "X", "Obs": []}}, status=200)

    client.get_series(["X"])

    query = responses.calls[0].request.url
    assert "pass=pw" in query
    assert "token=" not in query


@responses.activate
def test_single_series_returned_as_dict_is_handled():
    """BCCh returns a bare dict rather than a list when one series is asked for."""
    client = make_client(token="t")
    responses.add(
        responses.GET,
        MOCK_URL,
        json={
            "Series": {
                "seriesId": "ONE",
                "Obs": {"indexDateString": "01-01-2026", "value": "5", "statusCode": "OK"},
            }
        },
        status=200,
    )

    df = client.get_series(["ONE"])
    assert len(df) == 1
    assert df.iloc[0]["seriesId"] == "ONE"


@responses.activate
def test_blank_values_become_null_not_error():
    client = make_client(token="t")
    responses.add(
        responses.GET,
        MOCK_URL,
        json={
            "Series": {
                "seriesId": "X",
                "Obs": [
                    {"indexDateString": "01-01-2026", "value": "", "statusCode": "ND"},
                    {"indexDateString": "02-01-2026", "value": "7.5", "statusCode": "OK"},
                ],
            }
        },
        status=200,
    )

    df = client.get_series(["X"])
    assert len(df) == 2
    assert pd.isna(df.iloc[0]["value"])
    assert df.iloc[1]["value"] == 7.5


@responses.activate
def test_get_series_api_error():
    client = make_client(user="test@example.com", password="password123")

    responses.add(
        responses.GET,
        MOCK_URL,
        json={"Codigo": 100, "Descripcion": "Invalid credentials or unauthorized series access"},
        status=200,
    )

    with pytest.raises(BCChAPIError) as excinfo:
        client.get_series(["F073.TCN.USD.N.O.D"])

    assert "error code 100" in str(excinfo.value)


@responses.activate
def test_client_error_is_not_retried():
    """A 4xx means the request is wrong; retrying it 5x just wastes ~30s."""
    client = make_client(token="bad")
    responses.add(responses.GET, MOCK_URL, json={"detail": "unauthorized"}, status=401)

    with pytest.raises(BCChAPIError):
        client.get_series(["X"])

    assert len(responses.calls) == 1, "4xx must not be retried"


def test_missing_credentials_raises(monkeypatch):
    import lib.config

    monkeypatch.setattr(lib.config, "settings", None)
    with pytest.raises(ValueError, match="credentials"):
        BCChAPIClient()
