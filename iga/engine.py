from copy import deepcopy
from dataclasses import dataclass
import os
import sys
import time
import cli
import enum
import random

class CellState(enum.Enum):
    """The state of a cell in a grid."""

    DEAD = 0
    ALIVE = 1
    SUPERPOSITION = 2 # wish i had a quantum computer

    def __str__(self):
        if self == CellState.DEAD:
            return " "
        elif self == CellState.ALIVE:
            return "█"
        else:
            return "⧫"

@dataclass(frozen=True, slots=True)
class Point:
    x: int
    y: int

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, other):
        return Point(self.x * other.x, self.y * other.y)
    
    def __truediv__(self, other):
        return Point(self.x / other.x, self.y / other.y)
    
    def __floordiv__(self, other):
        return Point(self.x // other.x, self.y // other.y)
    
    def __mod__(self, other):
        return Point(self.x % other.x, self.y % other.y)
    
    def __pow__(self, other):
        return Point(self.x ** other.x, self.y ** other.y)
    
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __ne__(self, other):
        return not self == other
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __bool__(self):
        return self.x != 0 or self.y != 0
    
    def __contains__(self, item):
        return item in (self.x, self.y)
    
    def __len__(self):
        return 2

@dataclass(slots=True)
class Engine:
    """The engine that runs the simulation."""

    config: cli.Config = None
    width: int = None
    height: int = None
    cells: list[list[CellState]] = None
    entangled: list[tuple[Point, Point]] = None

    def __post_init__(self):
        """Post-initialization hook."""
        random.seed(self.config.seed)
        self.entangled = self.entangled or []
        self.config = self.config or cli.Config()

        self.width = self.width or self.config.width
        self.height = self.height or self.config.height
        # based on the start alive probability, randomly generate the cells
        self.cells = self.cells or [[CellState.ALIVE if random.random() < self.config.start_alive_prob else CellState.DEAD for _ in range(self.width)] for _ in range(self.height)]

        if self.width <= 0:
            raise ValueError("width must be positive")
        if self.height <= 0:
            raise ValueError("height must be positive")
        if len(self.cells) != self.height:
            raise ValueError("number of rows must equal height")
        for row in self.cells:
            if len(row) != self.width:
                raise ValueError("number of columns must equal width")
            
    def __getitem__(self, key):
        """Get the cell at the given position."""
        y, x = key
        return self.cells[y % self.height][x % self.width]
    
    def __setitem__(self, key, value):
        """Set the cell at the given position."""
        y, x = key
        self.cells[y % self.height][x % self.width] = value

    def __iter__(self):
        """Iterate over the cells in the grid."""
        return iter(self.cells)
    
    def __repr__(self):
        """Get a string representation of the grid."""
        return f"Grid(width={self.width}, height={self.height}, cells={self.cells})"
    
    def __eq__(self, other):
        """Check if two grids are equal."""
        return self.width == other.width and self.height == other.height and self.cells == other.cells
    
    def __ne__(self, other):
        """Check if two grids are not equal."""
        return not self == other
    
    def __contains__(self, item):
        """Check if the grid contains the given cell."""
        return item in self.cells
    
    def get_neighbours(self, x, y) -> list[tuple[CellState, Point]]:
        """Get the neighbours of the cell at the given position."""
        return [
            (self[y - 1, x - 1], Point(x - 1, y - 1)),
            (self[y - 1, x], Point(x, y - 1)),
            (self[y - 1, x + 1], Point(x + 1, y - 1)),
            (self[y, x - 1], Point(x - 1, y)),
            (self[y, x + 1], Point(x + 1, y)),
            (self[y + 1, x - 1], Point(x - 1, y + 1)),
            (self[y + 1, x], Point(x, y + 1)),
            (self[y + 1, x + 1], Point(x + 1, y + 1)),
        ]
    
    def link(self, x1, y1, x2, y2):
        """Link two cells together."""
        
        # make sure both cells are not already linked
        for entanglement in self.entangled:
            if Point(x1, y1) in entanglement or Point(x2, y2) in entanglement:
                return
            
        # make sure both cells are not the same
        if (x1, y1) == (x2, y2):
            return
            
        self.entangled.append((Point(x1, y1), Point(x2, y2)))

    def unlink(self, x1, y1, x2, y2):
        """Unlink two cells."""
        if (Point(x1, y1), Point(x2, y2)) in self.entangled:
            self.entangled.remove((Point(x1, y1), Point(x2, y2)))

    def iterate(self):
        current_cells = self.cells
        next_cells = deepcopy(current_cells)

        for y in range(self.height):
            for x in range(self.width):
                neighbours = self.get_neighbours(x, y)
                alive_neighbours = sum(neighbour[0] == CellState.ALIVE for neighbour in neighbours)

                if current_cells[y % self.height][x % self.width] == CellState.DEAD and alive_neighbours in (3, 4):
                    next_cells[y % self.height][x % self.width] = CellState.ALIVE

                    if alive_neighbours == 4:
                        for neighbour in neighbours:
                            if neighbour[0] == CellState.ALIVE:
                                self.link(x, y, neighbour[1].x, neighbour[1].y)

                                # put into superposition
                                next_cells[y % self.height][x % self.width] = CellState.SUPERPOSITION
                                next_cells[neighbour[1].y % self.height][neighbour[1].x % self.width] = CellState.SUPERPOSITION

                elif current_cells[y % self.height][x % self.width] == CellState.ALIVE and (alive_neighbours > 5 or alive_neighbours < 2):
                    next_cells[y % self.height][x % self.width] = CellState.DEAD

                elif current_cells[y % self.height][x % self.width] == CellState.SUPERPOSITION and alive_neighbours > 0:
                    # collapse the superposition of the observed particle
                    next_cells[y % self.height][x % self.width] = random.choice([CellState.ALIVE, CellState.DEAD])

                    # check for entanglements
                    for entanglement in self.entangled:
                        if Point(x, y) in entanglement:
                            
                            # get the other cell
                            other_cell = entanglement[0] if entanglement[0] != Point(x, y) else entanglement[1]
                            other_cell_state = current_cells[other_cell.y % self.height][other_cell.x % self.width]
                            
                            if other_cell_state == CellState.SUPERPOSITION:
                                # collapse the other cell (in reality this would be the difference in spin between the two particles but our quantum states are binary)
                                next_cells[other_cell.y % self.height][other_cell.x % self.width] = CellState.DEAD if next_cells[y % self.height][x % self.width] == CellState.ALIVE else CellState.ALIVE

                            # unlink the two cells
                            self.unlink(x, y, other_cell.x, other_cell.y)

        # make it official
        if self.cells == next_cells:
            # if the cells are the same, we have reached a stable state
            self.config.max_iter = 0
            print("Stable state reached")
        self.cells = next_cells

    def display(self, iteration: int = 0, cur_sec_iter_count: int = 0):
        """Display the grid."""

        # make sure we overwrite the previous grid
        print_str = "\033[2J"
        print_str += "\n".join(["".join([str(cell) for cell in row]) for row in self.cells])
        status_str = f"Entangled: {len(self.entangled):>5} | Iteration: {iteration:>5} | Iterations per second: {cur_sec_iter_count:>5} | Seed: {self.config.seed:>5}"

        # Print the status string
        sys.stdout.write(f"{print_str}\n{status_str}\n")
        sys.stdout.flush()

    def loop(self):
        """Run the simulation."""

        last_iter_time = time.time()
        cur_sec_iter_count = 0
        cur_sec = time.time() // 1
        last_ips = 0
        iterations = 0
        sleep_time = 0
        while iterations < self.config.max_iter or self.config.max_iter == -1:
            self.display(iterations, last_ips)
            self.iterate()

            # sleep for the remaining time to get the desired iterations per second
            sleep_time = 1 / self.config.ips - (time.time() - last_iter_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

            last_iter_time = time.time()
            iterations += 1

            # update the iterations per second
            cur_sec_iter_count += 1
            if time.time() // 1 != cur_sec:
                last_ips = round(cur_sec_iter_count / (time.time() - cur_sec), 2)
                cur_sec_iter_count = 0
                cur_sec = time.time() // 1