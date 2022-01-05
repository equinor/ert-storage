import pandas as pd
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_less
from ert_storage.compute import calculate_misfits_from_pandas, misfits

# randomly generated 8 response values distributed in 5 realizations
responses_values = [
    [0.625, 0.44, 0.651, 0.373, 0.341, 0.265, 0.82, 0.181],
    [0.525, 0.989, 0.757, 0.025, 0.35, 0.823, 0.664, 0.256],
    [0.103, 0.322, 0.77, 0.101, 0.135, 0.741, 0.901, 0.415],
    [0.825, 0.312, 0.271, 0.285, 0.768, 0.759, 0.065, 0.199],
    [0.53, 0.954, 0.23, 0.582, 0.106, 0.173, 0.06, 0.951],
]

# pre-computed univariate misfits on 3 observation points
univariate_misfits_results = {
    0: [-12.1801, -68.8070, -88.2973],
    1: [-5.9049, -68.0625, -83.6615],
    2: [-5.2900, -86.9556, -74.24694],
    3: [
        -53.1440,
        -37.9456,
        -87.1733,
    ],
    4: [-59.2900, -89.6809, -46.6489],
}

summary_misfits_results = [
    169.2845,
    157.6289,
    166.4926,
    178.2630,
    195.6198,
]

observation = {
    "values": [1, 2, 3],
    "errors": [0.1, 0.2, 0.3],
    "x_axis": ["C", "E", "H"],
}


def _get_dummy_response_df():
    return pd.DataFrame(
        [np.random.rand(8)], columns=["A", "B", "C", "D", "E", "F", "G", "H"]
    )


def _get_dummy_observation_df():
    return pd.DataFrame(
        data={"values": observation["values"], "errors": observation["errors"]},
        index=observation["x_axis"],
    )


def test_misfits_computation():
    response_dict = {}
    for realization_index, values in enumerate(responses_values):
        response_dict[realization_index] = pd.DataFrame(
            [values], columns=["A", "B", "C", "D", "E", "F", "G", "H"]
        )

    observation_df = _get_dummy_observation_df()

    misfits_df = calculate_misfits_from_pandas(
        response_dict, observation_df, summary_misfits=False
    )

    for id_real in univariate_misfits_results:
        assert_array_almost_equal(
            univariate_misfits_results[id_real],
            misfits_df.loc[id_real].values.flatten(),
            decimal=4,
        )

    misfits_df = calculate_misfits_from_pandas(
        response_dict, observation_df, summary_misfits=True
    )

    assert_array_almost_equal(
        summary_misfits_results,
        misfits_df.values.flatten(),
        decimal=4,
    )


def test_misfits_observations_match_response_values():
    # response values are the same as observed values we expect zero misfits
    data_df = _get_dummy_response_df()
    observation_df = _get_dummy_observation_df()
    # set values to match observations
    data_df.loc[0, observation["x_axis"]] = observation_df["values"].values

    misfits_df = calculate_misfits_from_pandas(
        {0: data_df}, observation_df, summary_misfits=False
    )

    assert_array_almost_equal(
        np.zeros(3),
        misfits_df.values.flatten(),
        decimal=4,
    )


def test_misfits_increasing_observation_error():
    # increasing erros should provide lower values of misfits
    data_df = _get_dummy_response_df()
    observation_df = _get_dummy_observation_df()

    misfits_increased_error = {}
    for idx in range(3):
        # increase the error
        observation_df["errors"] += 1
        misfits_increased_error[idx] = (
            calculate_misfits_from_pandas(
                {0: data_df}, observation_df, summary_misfits=False
            )
            .abs()  # required as univariate misfits now come with a sign
            .values.flatten()
        )
    assert_array_less(misfits_increased_error[1], misfits_increased_error[0])
    assert_array_less(misfits_increased_error[2], misfits_increased_error[1])


def test_misfits_increasing_response_values():
    # increasing response values compared to observation mean should
    # provide higher values of misfits
    data_df = _get_dummy_response_df()
    observation_df = _get_dummy_observation_df()

    misfits_increased_responses = {}
    for idx in range(3):
        # set response values as observation values and add a constant
        data_df.loc[0, observation["x_axis"]] = observation_df["values"] + idx
        misfits_increased_responses[idx] = (
            calculate_misfits_from_pandas(
                {0: data_df}, observation_df, summary_misfits=False
            )
            .abs()  # required as univariate misfits now come with a sign
            .values.flatten()
        )
    assert_array_less(misfits_increased_responses[0], misfits_increased_responses[1])
    assert_array_less(misfits_increased_responses[1], misfits_increased_responses[2])
