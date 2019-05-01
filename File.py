import os
import pathlib
import time
from datetime import date
import sys


class File:
    path = ''  # abspath
    extension = ''
    size = 0
    last_access_date = ''

    def __init__(self, path):
        file_stats = os.stat(path)  # Make a syscall to os to get file stats
        # Get last access time
        self.last_access_date = time.ctime(file_stats.st_atime)
        self.path = path
        self.size = os.path.getsize(path)
        if sys.platform.startswith('win32' or 'nt'):  # Windows based system
            self.extension = pathlib.PureWindowsPath(path).suffix
        else:  # Unix based system
            self.extension = pathlib.PurePosixPath(path).suffix

    def __lt__(self, other):  # Comparator of the files by their sizes, used by the heap
        return self.size > other.size

    def get_time_since_last_access(self):  # @TODO fix this
        split = self.last_access_date.split()
        day = split[2]
        month = split[1]
        year = split[4]

        try:
            d0 = date.today()
            if type(day) is not None and type(year) is not None and type(month) is not None:
                d1 = date(int(year), self.get_month_as_integer(month), int(day))
            else:
                return None
            delta = (d1 - d0).days * -1
            return delta
        except ValueError:
            print('There has been a problem while parsing the last access date')

    @staticmethod
    def get_month_as_integer(month_as_string):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        for i in range(0, len(months)):
            if month_as_string == months[i]:
                return int(i)
