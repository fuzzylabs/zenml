#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
import pandas as pd
from sklearn.model_selection import train_test_split

from zenml.steps import Output, step


@step
def data_splitter(
    input: pd.DataFrame,
) -> Output(train=pd.DataFrame, test=pd.DataFrame,):
    """Splits the input dataset into train and test slices."""
    train, test = train_test_split(input, test_size=0.1, random_state=13)
    return train, test
