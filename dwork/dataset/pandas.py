import pandas as pd
import random
import math
from typing import Any
from .dataset import Dataset
from .attribute import Attribute
from ..ast.types import Array, Type
from ..mechanisms import geometric_noise, laplace_noise
from .pandas_helpers import (
    epsilon,
    epsilon_flip,
    discretize,
    randomize,
    sample_p,
    sample_p_breadth_first,
)
from ..ast.expression import Expression
from ..ast.functions import Length, Sum

import math


class PandasLength(Length):
    def true(self) -> Any:
        if not isinstance(self.dataset, PandasDataset):
            raise ValueError("expected a pandas dataset")
        return len(self.dataset.df)


class PandasAttribute(Attribute):
    def __init__(self, dataset, column):
        self.dataset = dataset
        self.column = column

    @property
    def type(self) -> Type:
        return Array(self.dataset.type(self.column))

    def len(self):
        """
        We use this unpythonic function to make all DP function calls look consistent.
        """
        return self.dataset.len()

    def sum(self):
        return Sum(self)

    def dp(self, epsilon: float) -> Any:
        raise NotImplementedError

    def true(self) -> Any:
        return self.dataset.df[self.column]

    def sensitivity(self) -> Any:
        dt = self.dataset.type(self.column)
        return dt.max - dt.min

    def __len__(self):
        return self.len()


class PandasDataset(Dataset):
    def __init__(self, schema, df, *args, **kwargs):
        super().__init__(schema, *args, **kwargs)
        self.df = df

    def len(self):
        return PandasLength(self)

    def __len__(self):
        return self.len()

    def __getitem__(self, item: str) -> PandasAttribute:
        return PandasAttribute(self, item)

    def randomized_sample(
        self,
        breadth_first=True,
        interleave=0.0,
        max_depth=3,
        min_depth=1,
        limit=None,
        method="flip",
        exclude=None,
        target=None,
    ):
        fds, mapping, reverse_mapping = discretize(self.df, exclude=exclude)
        pr = 0.5
        pf = 0.5
        flip = method == "flip"
        fdsr = randomize(fds, 0, pf, flip=flip)
        if breadth_first:
            return sample_p_breadth_first(
                mapping,
                reverse_mapping,
                fdsr,
                fds,
                pr,
                pf,
                flip=flip,
                forced_attributes=target,
                min_depth=min_depth,
                max_depth=max_depth,
                limit=limit,
                verbose=False,
                interleave=interleave,
            )
