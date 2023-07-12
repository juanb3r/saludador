import pytest
import json

from functions import saludador


def test_lambda_status_code(): 
    res = saludador.handler({}, {})
    assert res.get('statusCode') == 200
    expected = {
        "statusCode": 200,
        "body": "Hola desde lambda!"
    }
    assert expected == res

