import getpass
import sys
import ctypes
import os
import time
import heapq
from numpy import unicode

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

num_of_files = 0
extension_dictionary = {}  # this dictionary maps the extensions to the corresponding max heaps
not_recently_accessed_files = []  # not recently accessed files is a max heap, depending on file sizes


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
    global num_of_files
    num_of_files += amount


def add_to_dictionary(directory, abs_path):  # Creates a file obj from path and adds to heap
    for file in directory:
        try:
            f = File(os.path.join(abs_path, file))
            if f.extension in extension_dictionary.keys():  # check if the corresponding heap exists for extension x
                hashable_heap = extension_dictionary[f.extension]
                hashable_heap.total_size += f.size
                heapq.heappush(hashable_heap.heap, f)
            elif f.extension != '':  # if the heap does not exist, create and add with current file
                new_heap = HashableHeap(f.extension)
                new_heap.total_size = f.size
                extension_dictionary[f.extension] = new_heap
                heapq.heappush(extension_dictionary[f.extension].heap, f)
        except FileNotFoundError:
            print(os.path.join(abs_path, file))
            print('No permission')


def find_not_recently_accessed_files():
    print('Finding not recently accessed files...')
    for key, extension_heap in extension_dictionary.items():    # go through dictionary, printing each heap
        find_not_recently_accessed_file_in_heap(extension_heap)


def find_not_recently_accessed_file_in_heap(extension_heap):
    for file in extension_heap.heap:
        days_since_last_access = file.time_since_last_access

        if days_since_last_access is not None:
            if days_since_last_access > NOT_RECENTLY_ACCESSED_THRESHOLD:
                heapq.heappush(not_recently_accessed_files, file)


def set_root_dir():
    global ROOT_DIR

    if USER_OS.startswith('darwin'):  # darwin is MacOS X
        ROOT_DIR = '/Users/' + getpass.getuser()
    elif USER_OS.startswith('linux'):
        ROOT_DIR = '~'
    elif user_os_is_windows():
        ROOT_DIR = 'C:\\'  # @TODO: find the user files dir in Windows and use it instead to exclude os files
    else:
        print('Your OS is not supported')


def print_file(file_name):
    print('File: ' + file_name)


def is_hidden_dir(file_path):
    name = set_name(file_path)

    if USER_OS.startswith('win32' or 'nt'):
        return has_hidden_attribute(file_path)
    else:
        return name.startswith('.')


def set_name(file_path):
    split = file_path.split('\\') if user_os_is_windows() else file_path.split('/')

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
    plt.xticks(fontsize=20, fontweight='bold')
    plt.yticks(fontsize=20, fontweight='bold')
    plt.show()


def plot_extension_vs_totalsize_treemap():
    x, y = get_extension_to_size_array_tuples_sorted()

    # create a color palette, mapped to these values
    color_map = generate_blue_color_map(y)

    squarify.plot(label=x[0:19], sizes=y[0:19], color=color_map)
    plt.title("Extension Treemap by Size", fontsize=23, fontweight="bold")

    # Remove our axes and display the plot
    plt.axis('off')
    plt.show()


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
    heapq.heappop(not_recently_accessed_files)

    for i in range(0, 19):  # print the first 20 files with highest delete priority
        file = heapq.heappop(not_recently_accessed_files)
        print(str(i) + ') ' + file.path + ' time: ' + str(file.time_since_last_access)
              + ' size: ' + str(file.size) + ' delete priority: ' + str(file.delete_priority))


def sort_not_recently_accessed_based_on_importance_score():
    # sort the files with a function that calculates a priority to delete
    # based on coefficients FILE_SIZE_COEFFICIENT and LAST_ACCESS_DATE_COEFFICIENT
    not_recently_accessed_files.sort(key=lambda file: get_delete_priority(file))


def get_delete_priority(file):
    assign_priority_score(file)
    return file.delete_priority


def assign_priority_score(file):
    time_since_last_access = file.time_since_last_access
    file_size_normalized = normalize_file_size(file.size)
    delete_priority = time_since_last_access * LAST_ACCESS_DATE_COEFFICIENT \
                      + FILE_SIZE_COEFFICIENT * file_size_normalized
    file.delete_priority = delete_priority


def normalize_file_size(size):  # We need to normalize the file size in order to make it comparable with access date
    return size / NORMALIZATION_RATE


# TODO take these into a main file
set_root_dir()
start = time.time()
find_all_files_and_dirs(ROOT_DIR)
find_not_recently_accessed_files()
print_not_recently_accessed_files()
print_size_ext_pairs()
# print_all_files()
end = time.time()
print('Number of files found: ' + str(num_of_files))
time_passed = end - start
print('Analysis duration: ' + str(time_passed))
adjust_plot_style()
plot_extension_vs_totalsize_bar()
plot_extension_vs_totalsize_treemap()
