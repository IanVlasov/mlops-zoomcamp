#!/usr/bin/env python
# coding: utf-8

from typing import Union

import argparse
from pathlib import Path
import pickle
import pandas as pd

categorical = ['PUlocationID', 'DOlocationID']


def read_data(filename):

    df = pd.read_parquet(filename)
    
    df['duration'] = df.dropOff_datetime - df.pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60

    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')
    
    return df


def make_predictions(year: int, month: int, output_path: Union[str, Path]):
    with open('model.bin', 'rb') as f_in:
        dv, lr = pickle.load(f_in)

    df = read_data(f'https://nyc-tlc.s3.amazonaws.com/trip+data/fhv_tripdata_{year:04d}-{month:02d}.parquet')

    dicts = df[categorical].to_dict(orient='records')
    X_val = dv.transform(dicts)
    y_pred = lr.predict(X_val)

    print(f"Mean prediction for {year:04d}-{month:02d}: {y_pred.mean():.4f}")

    df['ride_id'] = f'{year:04d}/{month:02d}_' + df.index.astype('str')

    df_result = pd.DataFrame({"ride_id": df["ride_id"], "predictions": y_pred})

    df_result.to_parquet(
        output_path,
        engine='pyarrow',
        compression=None,
        index=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int, help="Year of the data to download")
    parser.add_argument("month", type=int, help="Month of the data to download")

    args = parser.parse_args()

    year = args.year
    month = args.month

    cwd = Path().cwd()
    results_path = cwd / "results"
    results_path.mkdir(parents=True, exist_ok=True)
    output_path = results_path / f"df_result_{year:04d}-{month:02d}.parquet"

    make_predictions(year, month, output_path=output_path)
