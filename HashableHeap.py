class HashableHeap:  # wrapper class for heaps, required for the extension based hashing
    heap = []
    extension = ''
    size = 0

    def __init__(self, extension):
        self.extension = extension

    def __hash__(self):
        hash(self.extension)

    def __lt__(self, other):  # Comparator of the heaps by their sizes
        return self.size > other.size
