import os
import os.path
from collections import deque


from threading import Lock


class SimpleBuffer:
    """
    Simple Implementation of a 'scrolling' buffer. The data container (a deque) initially grows to a maximum value given
    by self._size then for every point added on the right popleft() is called. A counter keeps track of how many new
    points have been added and after _size new points have been added the data is saved to Disk (if a flag is set).
    """
    def __init__(self, size: int, output_path: str, keywords: list, *, save: bool = False, header: str = ''):
        if size <= 0:
            raise ValueError(f"Buffer Size must be positive, got {size}")

        if keywords is None or len(keywords) == 0:
            raise ValueError("At least 1 keyword must be given")

        path, filepath = os.path.split(output_path)
        if len(path) != 0 and not os.path.exists(path):
            os.makedirs(path)

        self.header_extra = header

        self._size = size
        self._output_path = output_path

        self.containers = [deque() for _ in keywords]
        self._keywords = keywords
        # keeps track of how many points we add so that we know when to save
        self._new_points = 0
        # used in iteration
        self._iter_point = 0

        self._save = save
        self._lock = Lock()

    ####################
    # CLIENT INTERFACE #
    ####################
    def push_back(self, *args):
        with self._lock:
            if len(args) != len(self._keywords):
                raise ValueError(f"Not enough values to push in buffer: got {len(args)} required {len(self._keywords)}")

            for container, val in zip(self.containers, args):
                container.append(val)
            self._new_points += 1

            if len(self.containers[0]) > self._size:
                for container in self.containers:
                    container.popleft()

            if self._new_points >= self._size:
                if self._save:
                    self._write_data()
                self._new_points = 0

    def is_saving(self):
        return self._save

    def set_save(self, status: bool):
        with self._lock:
            self._save = status

    def close(self):
        if self._save:
            self._write_data()

    @property
    def filepath(self):
        return self._output_path

    @filepath.setter
    def filepath(self, value):
        with self._lock:
            path, filepath = os.path.split(value)
            if len(path) != 0 and not os.path.exists(path):
                os.makedirs(path)
            self._output_path = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        if value <= 0:
            raise ValueError(f"Buffer Size must be positive, got {value}")

        with self._lock:
            self._size = value
            # If necessary shrink the list (left side values go first)
            while len(self.containers[0]) > self._size:
                for container in self.containers:
                    container.popleft()

    #############
    # INTERNALS #
    #############
    def _write_header(self):
        with open(self._output_path, 'w+') as f_out:
            if self.header_extra:
                f_out.write(self.header_extra + '\n')
            names = [str(kw) for kw in self._keywords]
            f_out.write('#' + ",".join(names) + '\n')

    def _write_data(self):
        if not os.path.isfile(self._output_path):
            self._write_header()

        with open(self._output_path, 'a+') as f_out:
            for data in zip(*self.containers):
                line = ','.join([str(val) for val in data]) + '\n'
                f_out.write(line)

    def __str__(self):
        return self.containers.__str__()

    def __len__(self):
        return self.containers[0].__len__()

    def __getitem__(self, item):
        return [container.__getitem__(item) for container in self.containers]

    def __iter__(self):
        self._iter_point = 0
        return self

    def __next__(self):
        if self._iter_point >= self.__len__():
            raise StopIteration
        ret = self.__getitem__(self._iter_point)
        self._iter_point += 1
        return ret


if __name__ == '__main__':
    import numpy as np
    # generate a container
    cc = SimpleBuffer(100, '', ['time', 'counts'])

    # generate some data
    for i in range(20):
        cc.push_back(i, np.random.rand())

    # let's see it
    print(cc)
    # let's see the full container
    print(cc.containers)

    # test the save capabilities
    cc = SimpleBuffer(100, './test.out', ['time', 'counts'], save=True)

    # generate some data
    for i in range(200):
        cc.push_back(i, np.random.rand())
