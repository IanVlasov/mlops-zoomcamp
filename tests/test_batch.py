import batch


def test_prepare_data(prepare_input, prepare_expected):
    processed_df = batch.prepare_data(prepare_input, ['PUlocationID', 'DOlocationID'])
    assert processed_df.round(3).equals(prepare_expected.round(3))
