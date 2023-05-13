from dataclasses import dataclass, field
import time
from typing import Optional


@dataclass(slots=True)
class Config:
    """A configuration class for the IGA CLI.

    Attributes:
        width: The width of the initial grid
        height: The height of the initial grid
        max_iter: The maximum number of iterations
        ips: The number of iterations per second to run the simulation at
        seed: The seed to use for the random number generator
        start_alive_prob: The probability of a cell starting alive

    """
    width: int = 24
    height: int = 24
    max_iter: int = 100
    ips: int = 1
    seed: int = field(default_factory=time.time_ns)
    start_alive_prob: float = 0.5


def parse_args(args: list[str]) -> Config:
    """Parse the command line arguments.

    Args:
        args: The command line arguments

    Returns:
        The parsed configuration

    """
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "--width", type=int, default=24, help="the width of the grid"
    )
    parser.add_argument(
        "--height", type=int, default=24, help="the height of the grid"
    )
    parser.add_argument(
        "-m",
        "--max-iter",
        type=int,
        default=-1,
        help="the maximum number of iterations",
    )
    parser.add_argument(
        "-s",
        "--ips",
        type=int,
        default=9999999,
        help="the number of iterations per second to run the simulation at",
    )
    parser.add_argument(
        "--seed", type=int, default=time.time_ns(), help="the seed to use for the random number generator"
    )
    parser.add_argument(
        "-a",
        "--start-alive-prob",
        type=float,
        default=0.25,
        help="the probability of a cell starting alive",
    )

    return Config(**vars(parser.parse_args(args)))