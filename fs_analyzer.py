import getpass
import sys
import ctypes
import os
import datetime
import time
import heapq
import pathlib
from numpy import unicode


class File:
    path = ''
    extension = ''
    size = 0
    last_access_date = datetime.time   # @TODO learn how to define a date obj.

    def __init__(self, path):
        print(os.path.abspath(path))
        file_stats = os.stat(path)  # Make a syscall to os to get file stats
        # Get last access time
        self.last_access_date = time.ctime(file_stats.st_atime)
        self.path = path
        self.size = os.path.getsize(path)
        if sys.platform.startswith('win32' or 'nt'):    # Windows based system
            self.extension = pathlib.PureWindowsPath(path).suffix
        else:   # Unix based system
            self.extension = pathlib.PurePosixPath(path).suffix

    def __lt__(self, other):    # Comparator of the files by their sizes
        return self.size > other.size

    # def get_time_since_last_access(self):
    #     today = datetime.date.today()
    #     return today - self.last_access_date


special_dirs = ['Library']  # @TODO Make use of this.
user_os = sys.platform
num_of_files = 0
ROOT_DIR = ''
file_heap = []  # this is the heap to store File objects in sorted order of sizes


def find_all_files_and_dirs(root_dir):
    # root_dir is the parent of all dirs
    # go through dirs, we use top down approach to ignore hidden dirs with continue
    for path, dirs, files in os.walk(root_dir, topdown=True):
        files = [f for f in files if not is_hidden_dir(f)]
        dirs[:] = [d for d in dirs if not is_hidden_dir(d)]
        # special dirs is the list of os specific dirs in MacOS, Linux Dist. and Windows
        if os.path.isdir(path) or os.path.isfile(path):   # Current element is a directory or file
            for directory in dirs:
                find_all_files_and_dirs(directory)  # add dirs recursively

            add_to_heap(files, str(os.path.abspath(path))) # add the files inside the dir
            increment_file_count(len(files))    # Increment file count with number of files in dir
        else:   # It is a special file if its not either file nor dir
            print('Current element is a special file (Socket, FIFO, device file, ...)')

    print_files()


def print_files():
    for i in range(len(file_heap)):
        item = heapq.heappop(file_heap)
        print('name: ' + str(item.path) + ' size: ' + str(item.size) + ' extension: ' + str(item.extension))


def increment_file_count(amount):
    global num_of_files
    num_of_files += amount


def add_to_heap(directory, abs_path):  # Creates a file obj from path and adds to heap
    for file in directory:
        try:
            heapq.heappush(file_heap, File(abs_path + '/' + file))
        except FileNotFoundError:
            print('File not found!')


def set_root_dir():
    global ROOT_DIR

    if user_os.startswith('darwin'):  # darwin is MacOS X
        ROOT_DIR = '/Users/' + getpass.getuser()
    elif user_os.startswith('linux'):
        ROOT_DIR = '~'
    elif user_os.startswith('win32' or 'nt'):
        ROOT_DIR = 'C:\\'  # @TODO: find the user files dir in Windows and use it instead to exclude os files
    else:
        print('Your OS is not supported')


def print_file(file_name):
    print('File: ' + file_name)


def is_hidden_dir(file_path):
    name = set_name(file_path)

    if user_os.startswith('win32' or 'nt'):
        return has_hidden_attribute(file_path)
    else:
        return name.startswith('.')


def set_name(file_path):
    split = file_path.split('/')
    name = split[-1]   # take the last item

    return name


def has_hidden_attribute(filepath):
    try:
        attributes = ctypes.windll.kernel32.GetFileAttributesW(unicode(filepath))
        assert attributes != -1
    except (AttributeError, AssertionError):
        result = False
        return result


set_root_dir()
find_all_files_and_dirs(ROOT_DIR)
print(num_of_files)
