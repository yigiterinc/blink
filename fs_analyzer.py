import getpass
import os
import sys
import ctypes

from numpy import unicode

special_dirs = ['Library']
user_os = sys.platform
num_of_files = 0
num_of_dirs = 0


def print_all_files_and_dirs(): # @TODO there is a bug that is causing this function to ignore some dirs. Fix it.
    # root_dir is the parent of all dirs
    root_dir = get_root_dir()

    # go through dirs, we use top down approach to ignore hidden dirs with continue
    for name, dirs, files in os.walk(root_dir, topdown=True):
        files = [f for f in files if not is_hidden_dir(f)]
        dirs[:] = [d for d in dirs if not is_hidden_dir(d)]
        # special dirs is the list of os specific dirs in MacOS, Linux Dist. and Windows
        global num_of_dirs
        num_of_dirs += 1
        print_files_in_dir(name, files)


def get_root_dir():
    root_dir = ''

    if user_os.startswith('darwin'):  # darwin is MacOS X
        root_dir = '/Users/' + getpass.getuser()
    elif user_os.startswith('linux'):
        root_dir = '~'
    elif user_os.startswith('win32' or 'nt'):
        root_dir = 'C:\\'  # @TODO: find the user files dir in Windows and use it instead to exclude os files
    else:
        print("Your OS is not supported")
    return root_dir


def print_files_in_dir(dir_name, files):
    num_of_files_in_dir = 0
    for dir_name in files:
            num_of_files_in_dir += 1

    global num_of_files
    num_of_files += num_of_files_in_dir

    print('Found directory: ' + dir_name + ' with ' + str(num_of_files_in_dir) + ' files inside')


def is_hidden_dir(file_path):
    name = set_name(file_path)

    if user_os.startswith('win32' or 'nt'):
        return has_hidden_attribute(file_path)
    else:
        return name.startswith('.')


def set_name(file_path):
    split = file_path.split('/')
    name = split[len(split) - 1]

    return name


def has_hidden_attribute(filepath):
    try:
        attributes = ctypes.windll.kernel32.GetFileAttributesW(unicode(filepath))
        assert attributes != -1
    except (AttributeError, AssertionError):
        result = False
        return result


print_all_files_and_dirs()
