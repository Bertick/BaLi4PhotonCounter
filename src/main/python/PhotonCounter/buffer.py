import os
import os.path
from collections import deque


class Buffer:
    def __init__(self, size: int, output_path: str, keywords: list):
        if size <= 0:
            raise ValueError(f"Buffer Size must be positive, got {size}")

        if keywords is None or len(keywords) == 0:
            raise ValueError("At least 1 keyword must be given")

        path, filepath = os.path.split(output_path)
        if len(path) != 0 and not os.path.exists(path):
            os.makedirs(path)

        self._size = size
        self._output_path = output_path

        self._container = deque()
        self._keywords = keywords
        self._new_points = 0

    def _write_header(self):
        with open(self._output_path, 'w+') as f_out:
            names = [str(kw) for kw in self._keywords]
            f_out.write('#' + ",".join(names) + '\n')

    def _write_data(self):
        if not os.path.isfile(self._output_path):
            self._write_header()

        with open(self._output_path, 'a+') as f_out:
            for data in self._container:
                line = ','.join([str(val) for val in data]) + '\n'
                f_out.write(line)

    def push_back(self, *args):
        if len(args) != len(self._keywords):
            raise ValueError("Not enough values to push in buffer")

        if len(self._container) == self._size:
            # if we reached max size, pop leftmost data
            self._container.popleft()
        # add new data
        self._container.append(args)

        self._new_points += 1

        if self._new_points > self._size:
            self._write_data()
            self._new_points = 0

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        if value <= 0:
            raise ValueError(f"Buffer Size must be positive, got {value}")
        self._size = value

        while len(self._container) >= self._size:
            # delete older points
            self._container.popleft()



