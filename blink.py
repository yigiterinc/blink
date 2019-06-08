#!/usr/bin/env python3

import getpass
import sys
import ctypes
import os
import time
import heapq
from numpy import unicode
from collections import OrderedDict

# Project files
from File import File
from HashableHeap import HashableHeap

# Plotting related stuff
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import cycler
from matplotlib import colors
import squarify

# Constants
ROOT_DIR = ''
USER_OS = sys.platform
NOT_RECENTLY_ACCESSED_THRESHOLD = 30    # Files that have not been accessed in 30 days are not recently accessed
FILE_SIZE_COEFFICIENT = 80/100
LAST_ACCESS_DATE_COEFFICIENT = 20/100
NORMALIZATION_RATE = 1/100000

# Plot styles are overridden in adjust_plot_style function, hold a reference to defaults to reset if needed
IPython_default = ''

num_of_files_found = 0
total_size_of_found_files = 0

extension_dictionary = {}  # maps the extensions to the corresponding max heaps
# Holds number of of files in the following size bins:
# 0-1KB, 1-100KB, 100-500KB, 500KB-1MB, 1MB - 5MB, 5MB - 50MB, 50MB-100MB, 100MB-500MB, 500MB-1GB, 1GB-10GB, >10GB
count_to_size_bins = {"0-1KB": 0, "1KB-100KB": 0, "100KB-500KB": 0, "500KB-1MB": 0, "1MB-5MB": 0,
                      "5MB-50MB": 0, "50MB-100MB": 0, "100MB-500MB": 0, "500MB-1GB": 0, "1GB-10GB": 0, ">10GB": 0}
count_to_size_bins_cumulative = {}

# Holds total size of files in the following size bins:
# 0-1KB, 1-100KB, 100-500KB, 500KB-1MB, 1MB - 5MB, 5MB - 50MB, 50MB-100MB, 100MB-500MB, 500MB-1GB, 1GB-10GB, >10GB
total_size_to_size_bins = {"0-1KB": 0, "1KB-100KB": 0, "100KB-500KB": 0,
                           "500KB-1MB": 0, "1MB-5MB": 0, "5MB-50MB": 0, "50MB-100MB": 0,
                           "100MB-500MB": 0, "500MB-1GB": 0, "1GB-10GB": 0, ">10GB": 0}
total_size_to_size_bins_cumulative = {}

not_recently_accessed_files = []  # not recently accessed files is a max heap, depending on file sizes
top_20_not_recently_accessed = [None] * 21  # index 0 is empty 1..20 holds not recently used files

def find_all_files_and_dirs(root_dir):
    # root_dir is the parent of all dirs
    # go through dirs, we use top down approach to ignore hidden dirs with continue
    for path, dirs, files in os.walk(root_dir, topdown=True):
        files = [f for f in files if not is_hidden_dir(f)]
        dirs[:] = [d for d in dirs if not is_hidden_dir(d)]
        # special dirs is the list of os specific dirs in MacOS, Linux Dist. and Windows
        if os.path.isdir(path) or os.path.isfile(path):  # Current element is a directory or file
            add_to_dictionary(files, str(os.path.abspath(path)))  # add the files inside the dir
            increment_file_count(len(files))  # Increment file count with number of files in dir
        else:  # It is a special file if its not either file nor dir
            print('Current element is a special file (Socket, FIFO, device file, ...)')


def print_all_files():
    print('*** Printing all files ***')
    for key, extension_heap in extension_dictionary.items():    # go through dictionary, printing each heap
        print('--- Printing ' + key + ' items' + ' total size is: ' + str(extension_heap.total_size) + ' ---')
        print_heap(extension_heap)


def print_heap(extension_heap):
    for item in extension_heap.heap:
        print(item.path + ' size:' + str(item.size) + ' Time since last access: ' + str(
              str(item.time_since_last_access) + ' days'))


def print_size_ext_pairs():
    for key, extension_heap in extension_dictionary.items():
        print(key + ' - ' + 'Total size: ' + format_bytes(extension_heap.total_size))


def increment_file_count(amount):
    global num_of_files_found
    num_of_files_found += amount


def add_to_dictionary(directory, abs_path):  # Creates a file obj from path and adds to heap
    for file in directory:
        try:
            f = File(os.path.join(abs_path, file))
            # check the size and increment the frequency here
            add_to_bins(f)
            if f.extension in extension_dictionary.keys():  # check if the corresponding heap exists for extension x
                hashable_heap = extension_dictionary[f.extension]
                hashable_heap.total_size += f.size
                heapq.heappush(hashable_heap.heap, f)
            elif f.extension != '':  # if the heap does not exist, create and add with current file
                new_heap = HashableHeap(f.extension)
                new_heap.total_size = f.size
                extension_dictionary[f.extension] = new_heap
                heapq.heappush(extension_dictionary[f.extension].heap, f)
        except OSError:     # No permission
            pass


# Holds total size of files in the following size bins:
# 0-1KB, 1-100KB, 100-500KB, 500KB-1MB, 1MB - 5MB, 5MB - 50MB, 50MB-100MB, 100MB-500MB, 500MB-1GB, 1GB-10GB, >10GB
def add_to_bins(file):
    global total_size_of_found_files

    size_formatted = format_bytes(file.size)
    split = size_formatted.split()
    size = float(split[0])
    magnitude = split[1]
    total_size_of_found_files += file.size

    if magnitude[0:4] == "byte":
        total_size_to_size_bins["0-1KB"] += file.size
        count_to_size_bins["0-1KB"] += 1
    elif magnitude[0:4] == "Kilo":
        if int(size) < 100:
            total_size_to_size_bins["1KB-100KB"] += file.size
            count_to_size_bins["1KB-100KB"] += 1
        elif int(size) < 500:
            total_size_to_size_bins["100KB-500KB"] += file.size
            count_to_size_bins["100KB-500KB"] += 1
        else:
            total_size_to_size_bins["500KB-1MB"] += file.size
            count_to_size_bins["500KB-1MB"] += 1
    elif magnitude[0:4] == "Mega":
        if size < 5:
            total_size_to_size_bins["1MB-5MB"] += file.size
            count_to_size_bins["1MB-5MB"] += 1
        elif size < 50:
            total_size_to_size_bins["5MB-50MB"] += file.size
            count_to_size_bins["5MB-50MB"] += 1
        elif size < 100:
            total_size_to_size_bins["50MB-100MB"] += file.size
            count_to_size_bins["50MB-100MB"] += 1
        elif size < 500:
            total_size_to_size_bins["100MB-500MB"] += file.size
            count_to_size_bins["100MB-500MB"] += 1
        else:
            total_size_to_size_bins["500MB-1GB"] += file.size
            count_to_size_bins["500MB-1GB"] += 1
    elif magnitude[0:4] == "Giga":
        if size < 10:
            total_size_to_size_bins["1GB-10GB"] += file.size
            count_to_size_bins["1GB-10GB"] += 1
        else:
            total_size_to_size_bins[">10GB"] += file.size
            count_to_size_bins[">10GB"] += 1


def convert_bins_to_percentage():
    for key, value in count_to_size_bins.items():
        count_to_size_bins[key] = (value * 100) / num_of_files_found

    for key, value in total_size_to_size_bins.items():
        total_size_to_size_bins[key] = (value * 100) / total_size_of_found_files


def fill_cumulative_bins():
    global count_to_size_bins_cumulative
    global total_size_to_size_bins_cumulative

    count_to_size_bins_cumulative = OrderedDict(count_to_size_bins)
    total_size_to_size_bins_cumulative = OrderedDict(total_size_to_size_bins)

    previous = 0
    for key, value in count_to_size_bins_cumulative.items():
        count_to_size_bins_cumulative[key] = value + previous
        previous = count_to_size_bins_cumulative[key]

    previous = 0
    for key, value in total_size_to_size_bins_cumulative.items():
        total_size_to_size_bins_cumulative[key] = value + previous
        previous = total_size_to_size_bins_cumulative[key]


def print_distributions():
    print('Printing number of files among size ranges')
    for key, value in count_to_size_bins.items():
        print(key + ': ' + str(value) + ' files')

    print('Printing number of files among size ranges (Cumulative)')
    for key, value in count_to_size_bins_cumulative.items():
        print(key + ': ' + str(value) + ' files')

    print('Printing the total sizes of size bins')
    for key, value in total_size_to_size_bins.items():
        print(key + ', Total size: ' + format_bytes(value))

    print('Printing the total sizes of size bins (Cumulative)')
    for key, value in total_size_to_size_bins_cumulative.items():
        print(key + ', Total size: ' + format_bytes(value))


def print_distributions_percentage():
    print('Printing the percentages')

    for key, value in count_to_size_bins.items():
        print(key + ': ' + str(round(value, 2)) + '%')

    for key, value in count_to_size_bins_cumulative.items():
        print(key + ': ' + str(round(value, 2)) + '%')

    for key, value in total_size_to_size_bins.items():
        print(key + ', Total size: ' + str(round(value, 2)) + '%')

    for key, value in total_size_to_size_bins_cumulative.items():
        print(key + ', Total size: ' + str(round(value, 2)) + '%')


def find_not_recently_accessed_files():
    print('Finding not recently accessed files...')
    for key, extension_heap in extension_dictionary.items():    # go through dictionary, printing each heap
        find_not_recently_accessed_file_in_heap(extension_heap)


def find_not_recently_accessed_file_in_heap(extension_heap):
    for file in extension_heap.heap:
        days_since_last_access = file.time_since_last_access

        if days_since_last_access is not None:  # fill not recently used files heap
            if days_since_last_access > NOT_RECENTLY_ACCESSED_THRESHOLD:
                heapq.heappush(not_recently_accessed_files, file)


def fill_top_20_not_recently_accessed():
    for i in range(1, 21):
        file = heapq.heappop(not_recently_accessed_files)
        top_20_not_recently_accessed[i] = file


def set_default_root_dir():
    global ROOT_DIR

    if USER_OS.startswith('darwin'):  # darwin is MacOS X
        ROOT_DIR = '/Users/' + getpass.getuser()
    elif USER_OS.startswith('linux'):
        ROOT_DIR = '~'
    elif user_os_is_windows():
        ROOT_DIR = 'C:\\'  # @TODO: find the user files dir in Windows and use it instead to exclude os files
    else:
        print('Your OS is not supported')


def set_custom_root_dir(path):
    global ROOT_DIR
    ROOT_DIR = path


def print_file(file_name):
    print('File: ' + file_name)


def is_hidden_dir(file_path):
    name = set_name(file_path)

    if USER_OS.startswith('win32' or 'nt'):
        return has_hidden_attribute(file_path)
    else:
        return name.startswith('.')


def set_name(file_path):
    split = file_path.split('\\') \
        if user_os_is_windows() else file_path.split('/')

    name = split[-1]  # take the last item
    return name


def user_os_is_windows():
    return USER_OS.startswith('win32' or 'nt')


def has_hidden_attribute(filepath):
    try:
        attributes = ctypes.windll.kernel32.GetFileAttributesW(unicode(filepath))
        assert attributes != -1
    except (AttributeError, AssertionError):
        result = False
        return result


def adjust_plot_style():
    global IPython_default  # reference to the global var.
    IPython_default = plt.rcParams.copy()  # copy the default plot settings

    colors = cycler('color',
                    ['#EE6666', '#3388BB', '#9988DD',
                     '#EECC55', '#88BB44', '#FFBBBB'])
    plt.rc('axes', facecolor='#E6E6E6', edgecolor='none',
           axisbelow=True, grid=True, prop_cycle=colors)
    plt.rc('grid', color='w', linestyle='solid')
    plt.rc('xtick', direction='out', color='gray')
    plt.rc('ytick', direction='out', color='gray')
    plt.rc('patch', edgecolor='#E6E6E6')
    plt.rc('lines', linewidth=2)


def plot_extension_vs_totalsize_bar():
    x, y = get_extension_to_size_array_tuples_sorted()

    plt.figure(figsize=(30, 20))  # width:20, height:3
    plt.bar(x[0:19], y[0:19], align='edge', width=0.8)  # graph the largest sized 20 extensions
    plt.title("Extension Distribution by Size", fontsize=23, fontweight="bold")
    plt.xlabel('Extensions', fontsize=25)
    plt.ylabel('Total Size (MB)', fontsize=25)
    plt.xticks(fontsize=8, fontweight='bold')
    plt.yticks(fontsize=8, fontweight='bold')
    plt.show()


def plot_extension_vs_totalsize_treemap():
    x, y = get_extension_to_size_array_tuples_sorted()

    # create a color palette, mapped to these values
    color_map = generate_blue_color_map(y)

    try:
        squarify.plot(label=x[0:19], sizes=y[0:19], color=color_map)
        plt.title("Extension Treemap by Size", fontsize=23, fontweight="bold")

        # Remove our axes and display the plot
        plt.axis('off')
        plt.show()
    except Exception:
        print('An unexpected error occurred while displaying the treemap')


def generate_blue_color_map(data_set):
    cmap = matplotlib.cm.Blues
    min_value = min(data_set)
    max_value = max(data_set)
    norm = matplotlib.colors.Normalize(vmin=min_value, vmax=max_value)
    return [cmap(norm(value)) for value in data_set]


def get_extension_to_size_array_tuples_sorted():
    x = []
    y = []

    for w in sorted(extension_dictionary, key=extension_dictionary.get):
        x.append(w)
        y.append(extension_dictionary[w].total_size / 1000000)

    return x, y


def format_bytes(size):
    # 2**10 = 1024
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'Kilo', 2: 'Mega', 3: 'Giga', 4: 'Tera'}
    while size > power:
        size /= power
        n += 1
    return str(size) + ' ' + power_labels[n] + 'bytes'


def print_not_recently_accessed_files():
    sort_not_recently_accessed_based_on_importance_score()
    i = 1

    for file in top_20_not_recently_accessed:
        if file:
            print(str(i) + ') ' + file.path)
            i += 1


def sort_not_recently_accessed_based_on_importance_score():
    # sort the files with a function that calculates a priority to delete
    # based on coefficients FILE_SIZE_COEFFICIENT and LAST_ACCESS_DATE_COEFFICIENT
    not_recently_accessed_files.sort(key=lambda file: get_delete_priority(file))


def get_delete_priority(file):
    assign_priority_score(file)
    return file.delete_priority


def assign_priority_score(file):
    time_since_last_access = file.time_since_last_access
    file_size_normalized = file.size * NORMALIZATION_RATE
    delete_priority = time_since_last_access * LAST_ACCESS_DATE_COEFFICIENT \
                      + FILE_SIZE_COEFFICIENT * file_size_normalized
    file.delete_priority = delete_priority


def plot_count_to_size_distribution():
    x = []
    y = []

    for key, value in count_to_size_bins.items():
        x.append(key)
        y.append(value)

    plt.figure(figsize=(15, 7))
    plt.bar(x, y, align='edge', width=0.8)
    plt.title("File count % to size range", fontsize=23, fontweight="bold")
    plt.xlabel('Range', fontsize=25)
    plt.ylabel('Percentage of files covered (%)', fontsize=25)
    plt.xticks(fontsize=8, fontweight='bold')
    plt.yticks(fontsize=8, fontweight='bold')
    plt.show()


def plot_total_size_to_size_range_distribution():
    x = []
    y = []

    for key, value in total_size_to_size_bins.items():
        x.append(key)
        y.append(value)

    plt.figure(figsize=(15, 7))
    plt.bar(x, y, align='edge', width=0.8)
    plt.title('Total size % to size range', fontsize=15)
    plt.xlabel('Range', fontsize=25)
    plt.ylabel('Total Size in Range (%)', fontsize=25)
    plt.xticks(fontsize=8, fontweight='bold')
    plt.yticks(fontsize=8, fontweight='bold')
    plt.show()


def plot_count_to_size_distribution_cumulative():
    x = []
    y = []

    for key, value in count_to_size_bins_cumulative.items():
        x.append(key)
        y.append(value)

    plt.figure(figsize=(15, 7))
    plt.bar(x, y, align='edge', width=0.8)
    plt.title("File count % to size range (Cumulative)", fontsize=23, fontweight="bold")
    plt.xlabel('Range', fontsize=25)
    plt.ylabel('Percentage of files covered (%)', fontsize=25)
    plt.xticks(fontsize=8, fontweight='bold')
    plt.yticks(fontsize=8, fontweight='bold')
    plt.show()


def plot_size_range_to_total_size_distribution_cumulative():
    x = []
    y = []

    for key, value in total_size_to_size_bins_cumulative.items():
        x.append(key)
        y.append(value)

    plt.figure(figsize=(15, 7))
    plt.bar(x, y, align='edge', width=0.8)
    plt.title("Total size % to size range (Cumulative)", fontsize=23, fontweight="bold")
    plt.xlabel('Range', fontsize=25)
    plt.ylabel('Total size covered (%)', fontsize=25)
    plt.xticks(fontsize=8, fontweight='bold')
    plt.yticks(fontsize=8, fontweight='bold')
    plt.show()


def remove_unused_file():
    confirm = input("Are you sure you want to delete this file? Type 'y' to proceed, 'r' to return\n")
    while confirm == 'y':
        index = input("Type the index of the file you want to delete\n")
        os.remove(top_20_not_recently_accessed[int(index)].path)
        confirm = input('Continue deleting? Type y or n \n')


def read_command():
    command = input("Type 'show_size_stats' to see the distribution of files among different size bins, \n" +
                    "'show_extension_stats' to see the distribution of files among different extensions \n" +
                    "and 'run_cleaner' to see advices about which files are unused and may be deleted, \n" +
                    "type 'quit' to exit\n")
    print(command)
    return command


def main():
    print("Welcome to blink file system analyzer")
    print("Starting the analysis, this may take a while...")
    start = time.time()
    find_all_files_and_dirs(ROOT_DIR)
    end = time.time()
    time_passed = end - start
    print('Analysis duration: ' + str(time_passed))
    print('Number of files found: ' + str(num_of_files_found)
          + ' with total size of: ' + format_bytes(total_size_of_found_files))

    command = ''

    while command != 'quit':
        command = read_command()

        if command == 'show_size_stats':
            fill_cumulative_bins()
            print_distributions()
            plot_count_to_size_distribution()
            plot_total_size_to_size_range_distribution()
            convert_bins_to_percentage()
            fill_cumulative_bins()
            plot_count_to_size_distribution_cumulative()
            plot_size_range_to_total_size_distribution_cumulative()
            print_distributions_percentage()
        elif command == 'show_extension_stats':
            print_size_ext_pairs()
            adjust_plot_style()
            plot_extension_vs_totalsize_bar()
            plot_extension_vs_totalsize_treemap()
        elif command == 'run_cleaner':
            find_not_recently_accessed_files()
            fill_top_20_not_recently_accessed()
            print_not_recently_accessed_files()
            index = input("Type the index of the file you want to delete to remove or type 'r' to return\n")

            if index != 'r':
                while int(index) > 20 or int(index) < 1 and index != 'r':
                    index = input("Invalid input, try again, r to return \n")
                else:
                    remove_unused_file()

    print('Goodbye!')


if __name__ == '__main__':
    if len(sys.argv) == 1:    # If the user did not pass any path, use the defaults
        set_default_root_dir()
    else:
        set_custom_root_dir(sys.argv[1])

    main()