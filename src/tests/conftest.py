import logging
import warnings
from typing import *

import numpy as np
import pandas as pd
import pytest
from lightgbm.sklearn import LGBMRegressor
from sklearn.ensemble import AdaBoostRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor, ExtraTreeRegressor

from tests import read_test_config
from tests.paths import TEST_DATA_CSV
from yieldengine.loading.sample import Sample
from yieldengine.modeling.factory import (
    ModelPipelineFactory,
    SimplePreprocessingPipelineFactory,
)
from yieldengine.modeling.selection import Model

logging.basicConfig(level=logging.INFO)

warnings.filterwarnings(
    "ignore", message=r"Starting from version 2", category=UserWarning
)


@pytest.fixture
def batch_table() -> pd.DataFrame:

    # Note: this file is not included within the git repository!
    inputfile_config = read_test_config(section="inputfile")
    return pd.read_csv(
        filepath_or_buffer=TEST_DATA_CSV,
        delimiter=inputfile_config["delimiter"],
        header=inputfile_config["header"],
        decimal=inputfile_config["decimal"],
    )


@pytest.fixture
def regressor_grids() -> List[Model]:
    RANDOM_STATE = {"random_state": [42]}
    return [
        Model(
            estimator=LGBMRegressor(),
            parameter_grid={
                "max_depth": [5, 10],
                "min_split_gain": [0.1, 0.2],
                "num_leaves": [50, 100, 200],
                **RANDOM_STATE,
            },
        ),
        Model(
            estimator=AdaBoostRegressor(),
            parameter_grid={"n_estimators": [50, 80], **RANDOM_STATE},
        ),
        Model(
            estimator=RandomForestRegressor(),
            parameter_grid={"n_estimators": [50, 80], **RANDOM_STATE},
        ),
        Model(
            estimator=DecisionTreeRegressor(),
            parameter_grid={
                "max_depth": [0.5, 1.0],
                "max_features": [0.5, 1.0],
                **RANDOM_STATE,
            },
        ),
        Model(
            estimator=ExtraTreeRegressor(),
            parameter_grid={"max_depth": [5, 10, 12], **RANDOM_STATE},
        ),
        Model(estimator=SVR(), parameter_grid={"gamma": [0.5, 1], "C": [50, 100]}),
        Model(
            estimator=LinearRegression(), parameter_grid={"normalize": [False, True]}
        ),
    ]


@pytest.fixture
def sample(batch_table: pd.DataFrame) -> Sample:
    # drop columns that should not take part in modeling
    batch_table = batch_table.drop(columns=["Date", "Batch Id"])

    # replace values of +/- infinite with n/a, then drop all n/a columns:
    batch_table = batch_table.replace([np.inf, -np.inf], np.nan).dropna(
        axis=1, how="all"
    )

    sample = Sample(observations=batch_table, target_name="Yield")
    return sample


@pytest.fixture
def preprocessing_pipeline_factory(sample: Sample) -> ModelPipelineFactory:
    # define a ColumnTransformer to pre-process:
    # define a sklearn Pipeline step, containing the preprocessor defined above:
    return SimplePreprocessingPipelineFactory(
        impute_mean=sample.features_by_type(dtype=sample.DTYPE_NUMERICAL),
        one_hot_encode=sample.features_by_type(dtype=sample.DTYPE_OBJECT),
    )
