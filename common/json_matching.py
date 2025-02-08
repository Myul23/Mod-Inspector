from os.path import exists
from time import time
from threading import Thread, Lock

from json import load, dumps, dump
from sortedcontainers import SortedListWithKey
from queue import Queue, Empty
from copy import deepcopy


from sentence_transformers import SentenceTransformer, util
from gensim.models import KeyedVectors


class JsonMatching:
    def __init__(
        self,
        model_flag: bool = True,
        model_path: str = None,
        similarities_address: str = "similarities.json",
        pathes_address: str = "optimal_pathes.json",
    ):
        self.model_flag = model_flag
        self.__init_model(model_path=model_path)
        self.similarities_address = similarities_address
        self.__init_similarities()
        self.pathes_address = pathes_address
        self.__init_pathes()

    def __init_similarities(self) -> None:
        self.similarities = dict()
        if not exists(self.similarities_address):
            return

        with open(self.similarities_address, "r") as jf:
            self.similarities = load(jf)

    def __init_pathes(self) -> None:
        self.optimal_pathes = dict()
        if not exists(self.pathes_address):
            return

        with open(self.pathes_address, "r") as jf:
            data = load(jf)
        self.optimal_pathes.update({eval(key): value for key, value in data.items()})

    def __init_model(self, model_path: str) -> None:
        if self.model_flag:
            self.model = SentenceTransformer("all-MiniLM-L6-v2" if model_path is None else model_path)
            return

        self.model = KeyedVectors.load_word2vec_format(
            "GoogleNews-vectors-negative300.bin.gz" if model_path is None else model_path, binary=True
        )

    def change_model(self, model_flag: bool = False, model_path: str = None) -> None:
        self.model_flag = model_flag
        self.__init_model(model_path=model_path)

    def __get_keys(self, target: dict) -> list:
        queue = (
            [(key, target, [key]) for key in target.keys()]
            if isinstance(target, dict)
            else [(idx, target, [idx]) for idx in range(len(target))] if isinstance(target, list) else []
        )
        target_keys = dict()

        while len(queue) > 0:
            key, base, path = queue.pop(0)

            indexes = (
                base[key].keys()
                if isinstance(base[key], dict)
                else [idx for idx, k in enumerate(base[key]) if isinstance(k, dict)] if isinstance(base[key], list) else []
            )

            # * grouped values
            if len(indexes) > 0:
                for idx in indexes:
                    p = deepcopy(path)
                    p.append(idx)
                    queue.append((idx, base[key], p))
                continue

            # * single value
            if key in target_keys.keys():
                index = 1
                k = f"{key}_{index}"
                while k in target_keys.keys():
                    index += 1
                    k = f"{key}_{index}"
                target_keys[k] = path
            else:
                target_keys[key] = path
        return target_keys

    def get_keys(self, target: dict, deep: bool = True) -> list:
        if not deep:
            return list(target.keys())
        return self.__get_keys(target)

    def __similarity(self, key1: str, key2: str) -> float:
        # // 1 vs 1 matching, develop for 1 vs N matching preventing from double-encoded
        if self.model_flag:
            key1 = self.model.encode(key1)
            key2 = self.model.encode(key2)
            value = util.cos_sim(key1, key2).item()
        else:
            value = self.model.similarity(key1, key2)
        return round(value, 4)

    def get_similarity(self, base: list, target: list, census: bool = False, similarity_standards: float = 0.6) -> dict:
        similarities = {key: dict() for key in base}
        for base_key in base:
            for target_key in target:
                similarities[base_key][target_key] = (
                    self.similarities[base_key][target_key]
                    if base_key in self.similarities.keys() and target_key in self.similarities[base_key].keys()
                    else self.__similarity(base_key, target_key)
                )

                if not census and similarities[base_key][target_key] < similarity_standards:
                    similarities[base_key].pop(target_key)
            if len(similarities[base_key]) < 1:
                similarities.pop(base_key)
        return similarities

    def __init_defaults(self, table: dict) -> tuple:
        defaults = [0, {}]
        for start in table.keys():
            if len(table[start].keys()) > 1:
                continue
            for end, value in table[start].items():
                defaults[0] += value
                defaults[1].update({start: end})

        default_starts = set(table.keys()) - set(defaults[1].keys())
        default_ends = {end for start in table for end in table[start]} - set(defaults[1].values())

        queue = Queue()
        queue.put(defaults)
        pathes = SortedListWithKey(key=lambda x: x[0])
        pathes.add(tuple(defaults))

        return default_starts, default_ends, queue, pathes

    def __find_optimal_path(self, table: dict, num_threads: int = 8) -> None | dict:
        default_starts, default_ends, queue, pathes = self.__init_defaults(table)

        lock = Lock()

        def worker() -> None:
            while True:
                try:
                    value, determined_path = queue.get(timeout=1)
                except Empty:
                    return

                starts = tuple(default_starts - set(determined_path.keys()))
                ends = tuple(default_ends - set(determined_path.values()))
                if (starts, ends) in self.optimal_pathes.keys():
                    value += self.optimal_pathes[(starts, ends)][0]
                    determined_path.update(self.optimal_pathes[(starts, ends)][1])
                    pathes.add((value, determined_path))
                    continue

                for start in starts:
                    for end in ends:
                        if end not in table[start].keys():
                            continue

                        v = value + table[start][end]
                        d_path = deepcopy(determined_path)
                        d_path.update({start: end})

                        pathes.add((v, d_path))
                        queue.put((v, d_path))

                        k = (tuple(d_path.keys()), tuple(d_path.values()))
                        with lock:
                            self.optimal_pathes[k] = (
                                (max(v, self.optimal_pathes[k][0]), d_path) if k in self.optimal_pathes.keys() else (v, d_path)
                            )

        threads = []
        for _ in range(num_threads):
            thread = Thread(target=worker, args=())
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return pathes.pop() if len(pathes) > 0 else None

    def matching(self, base: dict | list, target: dict | list, deep_flag: bool = False, similarity_flag: bool = False) -> dict | list:
        base_keys = self.get_keys(base, deep=deep_flag) if isinstance(base, dict) else base
        target_keys = self.get_keys(target, deep=deep_flag) if isinstance(target, dict) else target

        start = time()
        similarities = self.get_similarity(base_keys.keys(), target_keys.keys())
        print(f"Similarity matrix calculation finish ({round(time() - start, 4)}s)")

        start = time()
        optimal_matching = self.__find_optimal_path(similarities)
        print(f"Optimal matching finish ({round(time() - start, 4)}s)")

        # ? save optimal matching results
        self.similarities.update(similarities)
        with open(self.similarities_address, "w") as jf:
            dump(self.similarities, jf, indent=2)
        data = dumps({str(k): (v, p) for k, (v, p) in self.optimal_pathes.items()}, indent=2)
        with open(self.pathes_address, "w") as jf:
            jf.write(data)

        return [similarities, optimal_matching][1 - similarity_flag :]


if __name__ == "__main__":
    json_matching = JsonMatching()

    left = {"apple": 1, "banana": 2}
    right = {"kiwis": 7, "orange": 4, "apples": 3}

    # from json_comfortables import Read_Json

    # read_json = Read_Json()
    # left = read_json.read("X://0. Stardew Valley Backup/0. sample/[CP] Motungi with Cafe v1.1.0/data/Shops/Blacksmith.json")
    # right = read_json.read("X://0. Stardew Valley Backup/0. sample/[CP] Motungi with Cafe v1.1.0/data/Shops/Traveler.json")

    print(json_matching.matching(left, right, deep_flag=True))
