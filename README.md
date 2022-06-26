# mlops-zoomcamp

To run docker:

    docker build -t fhv-taxi-ride-prediction .
    docker run --rm -v "$(pwd)"/results:/app/results fhv-taxi-ride-prediction 2021 04