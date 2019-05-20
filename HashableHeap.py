class HashableHeap:  # wrapper class for heaps, required for the extension based hashing
    def __init__(self, extension):
        self.heap = []
        self.total_size = 0
        self.extension = extension

    def __hash__(self):
        hash(self.extension)

    def __lt__(self, other):  # Comparator of the heaps by their sizes
        return self.total_size > other.total_size
