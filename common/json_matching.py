from copy import deepcopy
from sortedcontainers import SortedDict, SortedListWithKey

from sentence_transformers import SentenceTransformer, util
from gensim.models import KeyedVectors


class JsonMatching:
    def __init__(self, model_flag: bool = True, model_path: str = None):
        self.model_flag = model_flag
        self.__init_model(model_path=model_path)
        self.pathes = SortedListWithKey(key=lambda x: x[0])

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

    def __get_keys(self, target: dict, keys: list = []) -> list:
        keys.extend(list(target.keys()))

        for key, value in target.items():
            if not isinstance(value, dict):
                continue

            for k in self.__get_keys(value, keys):
                key_input = f"{key}.{k}"
                index = 1
                while key_input in keys:
                    key_input = f"{key}.{k}_{index}"
                    index += 1
                keys.append(key_input)
        return keys

    def get_keys(self, target: dict, deep: bool = True) -> list:
        if not deep:
            return list(target.keys())
        return self.__get_keys(target)

    def __similarity(self, key1: str, key2: str) -> float:
        # // 1 vs 1 matching, develop for 1 vs N matching preventing from double-encoded
        if self.model_flag:
            key1 = self.model.encode(key1)
            key2 = self.model.encode(key2)
            return util.cos_sim(key1, key2)

        return self.model.similarity(key1, key2)

    def get_similarity(self, base: list, target: list) -> dict:
        similarities = {key: dict() for key in base}
        for base_key in base:
            for target_key in target:
                similarities[base_key][target_key] = self.__similarity(base_key, target_key)
        return similarities

    def __find_optimal_path(self, table: dict) -> tuple:
        values = SortedListWithKey(key=lambda x: x[0])
        for start in table.keys():
            without_start = deepcopy(table)
            del without_start[start]

            for end in table[start].keys():
                for value, path in self.pathes:
                    if path == SortedDict({start: end}):
                        values.add((value, path))
                        break
                else:
                    self.pathes.add((table[start][end], SortedDict({start: end})))

                    sub_table = deepcopy(without_start)
                    for sub_key in sub_table.keys():
                        del sub_table[sub_key][end]

                    value, path = self.__find_optimal_path(sub_table)
                    value += table[start][end]
                    path.update({start: end})

                    if (value, path) not in self.pathes:
                        self.pathes.add((value, path))
                    values.add((value, path))

        if len(values) > 0:
            return values.pop()
        return (0, SortedDict({}))

    def matching(self, base: dict | list, target: dict | list, deep_flag: bool = False, similarity_flag: bool = False) -> dict | tuple:
        base = self.get_keys(base, deep=deep_flag)
        target = self.get_keys(target, deep=deep_flag)
        similarities = self.get_similarity(base, target)

        if similarity_flag:
            return similarities, self.__find_optimal_path(similarities.copy())
        else:
            return self.__find_optimal_path(similarities.copy())


if __name__ == "__main__":
    json_matching = JsonMatching()
    print(json_matching.matching({"apple": 1, "banana": 2}, {"kiwis": 7, "orange": 4, "apples": 3}))
