import pickle
from pathlib import Path

from datetime import datetime
from dateutil.relativedelta import relativedelta

from urllib import request

import pandas as pd
import mlflow

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from prefect import flow, task, get_run_logger

FILEPATH = Path(__file__).parent
DATA_PATH = FILEPATH / "data"
MODELS_PATH = FILEPATH / "models"

DATA_PATH.mkdir(exist_ok=True, parents=True)
MODELS_PATH.mkdir(exist_ok=True, parents=True)

@task
def get_train_val_data(date: datetime) -> tuple[Path, Path]:
    base_url = "https://nyc-tlc.s3.amazonaws.com/trip+data/"

    train_date = date - relativedelta(months=+2)
    val_date = date - relativedelta(months=+1)

    train_name = f"fhv_tripdata_{train_date.year}-{str(train_date.month).zfill(2)}.parquet"
    val_name = f"fhv_tripdata_{val_date.year}-{str(val_date.month).zfill(2)}.parquet"

    for name in [train_name, val_name]:
        path = DATA_PATH / name
        if not path.exists():
            url = base_url + name
            _ = request.urlretrieve(url, DATA_PATH / name)
    
    return DATA_PATH / train_name, DATA_PATH / val_name
    
@task
def read_data(path):
    df = pd.read_parquet(path)
    return df

@task
def prepare_features(df, categorical, train=True):
    logger = get_run_logger()
    df['duration'] = df.dropOff_datetime - df.pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60
    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    mean_duration = df.duration.mean()
    if train:
        logger.info(f"The mean duration of training is {mean_duration}")
    else:
        logger.info(f"The mean duration of validation is {mean_duration}")
    
    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')
    return df

@task
def train_model(df, categorical):
    logger = get_run_logger()

    train_dicts = df[categorical].to_dict(orient='records')
    dv = DictVectorizer()
    X_train = dv.fit_transform(train_dicts) 
    y_train = df.duration.values

    logger.info(f"The shape of X_train is {X_train.shape}")
    logger.info(f"The DictVectorizer has {len(dv.feature_names_)} features")

    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred = lr.predict(X_train)
    mse = mean_squared_error(y_train, y_pred, squared=False)
    logger.info(f"The MSE of training is: {mse}")
    return lr, dv

@task
def run_model(df, categorical, dv, lr):
    logger = get_run_logger()
    val_dicts = df[categorical].to_dict(orient='records')
    X_val = dv.transform(val_dicts) 
    y_pred = lr.predict(X_val)
    y_val = df.duration.values

    mse = mean_squared_error(y_val, y_pred, squared=False)
    logger.info(f"The MSE of validation is: {mse}")
    return

@flow
def main(date: str = None):

    if not date:
        date = datetime.today()
    else:
        date = datetime.fromisoformat(date)
    train_path, val_path = get_train_val_data(date).result()

    categorical = ['PUlocationID', 'DOlocationID']

    df_train = read_data(train_path)
    df_train_processed = prepare_features(df_train, categorical)

    df_val = read_data(val_path)
    df_val_processed = prepare_features(df_val, categorical)

    # train the model
    lr, dv = train_model(df_train_processed, categorical).result()
    run_model(df_val_processed, categorical, dv, lr)

    date_str = date.strftime("%Y-%m-%d")
    
    model_path = MODELS_PATH / f"model-{date_str}.bin"
    dv_path = MODELS_PATH / f"dv-{date_str}.bin"

    with open(model_path, 'wb') as handle:
        pickle.dump(lr, handle)
    
    with open(dv_path, 'wb') as handle:
        pickle.dump(dv, handle)

from prefect.deployments import DeploymentSpec
from prefect.orion.schemas.schedules import CronSchedule
from prefect.flow_runners import SubprocessFlowRunner

DeploymentSpec(
    flow=main,
    name="model_training",
    schedule=CronSchedule(cron="0 9 15 * *"),
    flow_runner=SubprocessFlowRunner(),
    tags=["ml"]
)
