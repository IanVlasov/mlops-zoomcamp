import os

import batch


def test_integration(prepare_input):
    input_file = batch.get_input_path(2021, 1)
    output_file = batch.get_output_path(2021, 1)
    batch.save_data(prepare_input, input_file)

    os.chdir("..")
    os.system("python batch.py 2021 1")

    df_result = batch.read_data(output_file)
    assert df_result.predicted_duration.sum().round(2) == 69.29
