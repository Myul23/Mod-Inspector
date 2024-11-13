class Read_Json:
    def __init__(self, base: dict | list = None):
        if base is not None and not isinstance(base, (dict, list)):
            print("Base is neither dictionary nor list data type.")
            return
        self.base = base

    def __find_related_value(self, base: dict | list, target) -> list:
        idxes = base.keys() if isinstance(base, dict) else range(len(base)) if isinstance(base, list) else []
        for idx in idxes:
            if isinstance(base[idx], (dict, list)):
                result = self.__find_related_value(base[idx], target)
                if result is None:
                    continue
                result.insert(0, idx)
                return result
            elif isinstance(base[idx], str) and target in base[idx]:
                return [idx]

    def __find_value(self, base: dict | list, target) -> list:
        idxes = base.keys() if isinstance(base, dict) else range(len(base)) if isinstance(base, list) else []
        for idx in idxes:
            if isinstance(base[idx], (dict, list)):
                result = self.__find_value(base[idx], target)
                if result is None:
                    continue
                result.insert(0, idx)
                return result
            elif base[idx] == target:
                return [idx]

    def find_value(self, base: dict | list = None, target=None, related_flag: bool = False) -> list:
        base = self.base if base is None else base
        result = self.__find_related_value(base, target) if related_flag else self.__find_value(base, target)
        if result == None:
            print(target, "is not found.")
        return result

    def __list_extend(self, target_list: list) -> list:
        for idx in range(len(target_list)):
            if isinstance(target_list[idx], list):
                target_list.extend(self.__list_extend(target_list.pop(idx)))
        return target_list

    def __find_all_related(self, base: dict | list, target) -> list:
        total = []
        idxes = base.keys() if isinstance(base, dict) else range(len(base)) if isinstance(base, list) else []

        for idx in idxes:
            if isinstance(base[idx], (dict, list)):
                result = self.__find_all_related(base[idx], target)
                if result is None:
                    continue
                result.insert(0, idx)
                total.append(result)
            elif isinstance(base[idx], str) and target in base[idx]:
                return [idx]
        return None if len(total) < 1 else total

    def __find_all(self, base: dict | list, target) -> list:
        total = []
        idxes = base.keys() if isinstance(base, dict) else range(len(base)) if isinstance(base, list) else []

        for idx in idxes:
            if isinstance(base[idx], (dict, list)):
                result = self.__find_all(base[idx], target)
                if result is None:
                    continue
                result.insert(0, idx)
                total.append(result)
            elif base[idx] == target:
                return [idx]
        return None if len(total) < 1 else total

    def find_all(self, base: dict | list = None, target=None, related_flag: bool = False) -> list:
        base = self.base if base is None else base
        result = self.__find_all_related(base, target) if related_flag else self.__find_all(base, target)
        if result == None:
            print(target, "is not found.")
            return

        for idx in range(len(result)):
            if isinstance(result, list):
                result[idx] = self.__list_extend(result[idx])
        return result

    def similarity(self, left: dict, right: dict) -> float:
        print(left, right)
        right_keys = right.keys()
        return sum([r in left for r in right_keys]) / len(right_keys)

    def __merge_dictionaries(self, dicts: list):
        templates = [dicts.pop(0)]
        for target in dicts:
            similarity = [self.similarity(temp, target) for temp in templates]
            maximum = max(similarity)
            if maximum < 0.75:
                templates.append(target)
                continue

            max_index = similarity.index(maximum)
            for key, value in target.items():
                if key not in templates[max_index].keys() or templates[max_index][key] is None:
                    templates[max_index][key] = value
                elif isinstance(value, dict):
                    # * str + dict, dict + dict
                    # temp = [templates[max_index][key]] if isinstance(templates[max_index][key], dict) else []
                    temp = [templates[max_index][key]]
                    temp.append(target[key])
                    templates[max_index][key] = self.__merge_dictionaries(temp)
                elif isinstance(value, list):
                    dict_values = [v for v in value if isinstance(v, dict)]
                    if len(dict_values) < 1:
                        templates[max_index][key] = value
                    elif len(dict_values) < 2:
                        templates[max_index][key] = value[dict_values[0]]
                    else:
                        dict_values.extend(target[key])
                        templates[max_index][key] = self.__merge_dictionaries(dict_values)
                else:
                    templates[max_index][key] = value
        return templates

    def make_template(self, dicts: list = None, save_flag: bool = True, save_json_file: str = "templates.json") -> None:
        dicts = self.base if dicts is None else dicts
        dicts = list(dicts) if isinstance(dicts, dict) else dicts if isinstance(dicts, list) else []
        templates = dicts if len(dicts) < 2 else self.__merge_dictionaries(dicts)

        if save_flag:
            from json import dump

            with open(save_json_file, "w", encoding="UTF-8") as jf:
                dump(templates, jf, ensure_ascii=False, indent=2)
        else:
            print(templates)


if __name__ == "__main__":
    from jstyleson import load

    with open("before.json", encoding="UTF-8-SIG") as jf:
        data = load(jf)
    under_json = Read_Json(data)

    print(under_json.find_all(target="유리컵", related_flag=True))
    # under_json.make_template()
