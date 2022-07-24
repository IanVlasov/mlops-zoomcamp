import pytest
from datetime import datetime
import pandas as pd


def dt(hour, minute, second=0):
    return datetime(2021, 1, 1, hour, minute, second)


@pytest.fixture(name="prepare_input", scope="package")
def prepare_input_fixture():
    data = [
        (None, None, dt(1, 2), dt(1, 10)),
        (1, 1, dt(1, 2), dt(1, 10)),
        (1, 1, dt(1, 2, 0), dt(1, 2, 50)),
        (1, 1, dt(1, 2, 0), dt(2, 2, 1)),
    ]

    columns = ['PUlocationID', 'DOlocationID', 'pickup_datetime', 'dropOff_datetime']
    return pd.DataFrame(data, columns=columns)


@pytest.fixture(name="prepare_expected", scope="package")
def prepare_expected_fixture():
    data = [
        ("-1", "-1", dt(1, 2), dt(1, 10), 8.),
        ("1", "1", dt(1, 2), dt(1, 10), 8.),
    ]

    columns = ['PUlocationID', 'DOlocationID', 'pickup_datetime', 'dropOff_datetime', "duration"]
    return pd.DataFrame(data, columns=columns)