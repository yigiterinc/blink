import os
import pathlib
import time
from datetime import date
import sys


class File:
    def __init__(self, path):
        file_stats = os.stat(path)  # Make a syscall to os to get file stats
        # Get last access time
        self.last_access_date = time.ctime(file_stats.st_atime)
        self.path = path
        self.size = os.path.getsize(path)
        self.delete_priority = 0
        if sys.platform.startswith('win32' or 'nt'):  # Windows based system
            self.extension = pathlib.PureWindowsPath(path).suffix
        else:  # Unix based system
            self.extension = pathlib.PurePosixPath(path).suffix

        self.time_since_last_access = self.get_time_since_last_access(date.today())

    def __lt__(self, other):  # Comparator of the files by their sizes, used by the heap
        return self.size > other.size

    def get_time_since_last_access(self, today):
        split = self.last_access_date.split()
        day = split[2]
        month = split[1]
        year = split[4]

        months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

        try:
            if type(day) is not None and type(year) is not None and type(month) is not None:
                d1 = date(int(year), months[month], int(day))
                delta = today - d1
                return delta.days
        except ValueError:
            print('last_access_date: ' + self.last_access_date + ' parsed D / M / Y: '
                  + day + '/' + month + '/' + year)