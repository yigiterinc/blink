import getpass
import sys
import ctypes
import os
import time
import heapq
from numpy import unicode
from File import File
from HashableHeap import HashableHeap
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import cycler
from matplotlib import colors
import squarify

user_os = sys.platform
num_of_files = 0
ROOT_DIR = ''
extension_dictionary = {}  # this dictionary maps the extensions to the corresponding max heaps

# plot styles are overridden in adjust_plot_style function, hold a reference to defaults to reset if needed
IPython_default = ''


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
        print(key + ' - ' + 'Total size: ' + format_bytes(extension_heap.size))


def increment_file_count(amount):
    global num_of_files
    num_of_files += amount


def add_to_dictionary(directory, abs_path):  # Creates a file obj from path and adds to heap
    for file in directory:
        try:
            f = File(os.path.join(abs_path, file))
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
            print(os.path.join(abs_path, file))
            print('No permission')


def set_root_dir():
    global ROOT_DIR

    if user_os.startswith('darwin'):  # darwin is MacOS X
        ROOT_DIR = '/Users/' + getpass.getuser()
    elif user_os.startswith('linux'):
        ROOT_DIR = '~'
    elif user_os_is_windows():
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
    split = file_path.split('\\') if user_os_is_windows() else file_path.split('/')

    name = split[-1]  # take the last item
    return name


def user_os_is_windows():
    return user_os.startswith('win32' or 'nt')


def has_hidden_attribute(filepath):
    try:
        attributes = ctypes.windll.kernel32.GetFileAttributesW(unicode(filepath))
        assert attributes != -1
    except (AttributeError, AssertionError):
        result = False
        return result


def adjust_plot_style():
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
        y.append(extension_dictionary[w].size / 1000000)

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


# TODO take these into a main file
set_root_dir()
start = time.time()
find_all_files_and_dirs(ROOT_DIR)
print_size_ext_pairs()
end = time.time()
print('Number of files found: ' + str(num_of_files))
time_passed = end - start
print('Analysis duration: ' + str(time_passed))
adjust_plot_style()
plot_extension_vs_totalsize_bar()
plot_extension_vs_totalsize_treemap()


