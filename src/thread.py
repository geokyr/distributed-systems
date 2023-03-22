from concurrent.futures import ThreadPoolExecutor

from parameters import NUMBER_OF_THREADS

class Thread:
    def __init__(self):
        self.executor = ThreadPoolExecutor(NUMBER_OF_THREADS)

    def submitTask(self, function, temp, utxos):
        future = self.executor.submit(function, temp, utxos)
        return future
