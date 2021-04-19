import sys
from pydantic import BaseModel
from typing import Union

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal


class PriorConst(BaseModel):
    """
    Constant parameter prior
    """

    function: Literal["const"] = "const"
    value: float


class PriorTrig(BaseModel):
    """
    Triangular distribution parameter prior
    """

    function: Literal["trig"] = "trig"
    min: float
    max: float
    mode: float


class PriorNormal(BaseModel):
    """
    Normal distribution parameter prior
    """

    function: Literal["normal"] = "normal"
    mean: float
    std: float


class PriorLogNormal(BaseModel):
    """
    Log-normal distribution parameter prior
    """

    function: Literal["lognormal"] = "lognormal"
    mean: float
    std: float


class PriorTruncNormal(BaseModel):
    """
    Truncated normal distribution parameter prior
    """

    function: Literal["truncnormal"] = "truncnormal"
    mean: float
    std: float


class PriorStdNormal(BaseModel):
    """
    Standard normal distribution parameter prior

    Normal distribution with mean of 0 and standard deviation of 1
    """

    function: Literal["stdnormal"] = "stdnormal"


class PriorUniform(BaseModel):
    """
    Uniform distribution parameter prior
    """

    function: Literal["uniform"] = "uniform"
    min: float
    max: float


class PriorDUniform(BaseModel):
    """
    Discrete distribution parameter prior
    """

    function: Literal["duniform"] = "duniform"
    min: float
    max: float


class PriorLogUniform(BaseModel):
    """
    Logarithmic uniform distribution parameter prior
    """

    function: Literal["loguniform"] = "loguniform"
    min: float
    max: float


class PriorErf(BaseModel):
    """
    Error function distribution parameter prior
    """

    function: Literal["erf"] = "erf"


class PriorDErf(BaseModel):
    """
    Discrete error function distribution parameter prior
    """

    function: Literal["derf"] = "derf"


Prior = Union[
    PriorConst,
    PriorTrig,
    PriorNormal,
    PriorLogNormal,
    PriorTruncNormal,
    PriorStdNormal,
    PriorUniform,
    PriorDUniform,
    PriorLogUniform,
    PriorErf,
    PriorDErf,
]
