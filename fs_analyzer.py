import getpass
import sys
import ctypes
import os
import time
import heapq
from numpy import unicode
from File import File
from HashableHeap import HashableHeap

user_os = sys.platform
num_of_files = 0
ROOT_DIR = ''
extension_dictionary = {}  # this hash table (dictionary) hashes the extensions to the corresponding max heaps


def find_all_files_and_dirs(root_dir):
    # root_dir is the parent of all dirs
    # go through dirs, we use top down approach to ignore hidden dirs with continue
    for path, dirs, files in os.walk(root_dir, topdown=True):
        files = [f for f in files if not is_hidden_dir(f)]
        dirs[:] = [d for d in dirs if not is_hidden_dir(d)]
        # special dirs is the list of os specific dirs in MacOS, Linux Dist. and Windows
        if os.path.isdir(path) or os.path.isfile(path):  # Current element is a directory or file
            for directory in dirs:
                find_all_files_and_dirs(directory)  # add dirs recursively

            add_to_dictionary(files, str(os.path.abspath(path)))  # add the files inside the dir
            increment_file_count(len(files))  # Increment file count with number of files in dir
        else:  # It is a special file if its not either file nor dir
            print('Current element is a special file (Socket, FIFO, device file, ...)')


def print_all_files():
    for key, extension_heap in extension_dictionary.items():
        print('--- Printing ' + key + ' items' + ' total size is: ' + str(extension_heap.size) + ' ---')
        print_heap(extension_heap)


def print_heap(extension_heap):
    for item in extension_heap.heap:
        print(item.path + ' size:' + str(item.size) + ' Time since last access: ' + str(
            File.get_time_since_last_access(item)))


def print_size_ext_pairs():
    for key, extension_heap in extension_dictionary.items():
        print(key + ' - ' + 'total size: ' + str(extension_heap.size))


def increment_file_count(amount):
    global num_of_files
    num_of_files += amount


def add_to_dictionary(directory, abs_path):  # Creates a file obj from path and adds to heap
    for file in directory:
        try:
            f = File(abs_path + '/' + file)
            if f.extension in extension_dictionary.keys():  # check if the corresponding heap exists for extension x
                hashable_heap = extension_dictionary[f.extension]
                hashable_heap.size += f.size
                heapq.heappush(hashable_heap.heap, f)
            elif f.extension != '':  # if the heap does not exist, create and add with current file
                new_heap = HashableHeap(f.extension)
                new_heap.size = f.size
                heapq.heappush(new_heap.heap, f)
                extension_dictionary[f.extension] = new_heap
        except FileNotFoundError:
            print(abs_path + '/' + file)
            print('No permission')


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
    name = split[-1]  # take the last item

    return name


def has_hidden_attribute(filepath):
    try:
        attributes = ctypes.windll.kernel32.GetFileAttributesW(unicode(filepath))
        assert attributes != -1
    except (AttributeError, AssertionError):
        result = False
        return result


set_root_dir()
start = time.time()
find_all_files_and_dirs(ROOT_DIR)
print_size_ext_pairs()
end = time.time()
print(num_of_files)
time_passed = end - start
print(time_passed)
