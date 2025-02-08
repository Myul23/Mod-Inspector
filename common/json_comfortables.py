from jstyleson import load, dump


class Read_Json:
    def __init__(self, address: str = None, base: dict | list = None):
        if address is not None:
            self.base = self.read(address)
        elif base is not None and not isinstance(base, (dict, list)):
            print("Base is neither dictionary nor list data type.")
            return
        else:
            self.base = base

    def read(self, address: str) -> dict:
        with open(address, encoding="UTF-8-SIG") as jf:
            data = load(jf)
        return data

    def append(self, dicts: dict | list, target: dict, list_flag: bool = False) -> dict | list:
        if dicts is None:
            return [target] if list_flag else target

        if isinstance(target, list):
            dicts.extend(target)
        else:
            dicts.append(target)
        return dicts

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

    def similarity(self, left: dict, right: dict, small_flag: bool = False) -> float:
        if len(left.keys()) > len(right.keys()):
            if not small_flag:
                temp = left.copy()
                left = right.copy()
                right = temp
        elif small_flag:
            temp = left.copy()
            left = right.copy()
            right = temp

        right_keys = right.keys()
        return sum([r in left for r in right_keys]) / len(right_keys)

    def __merge_dictionaries(self, dicts: list) -> list:
        templates = [dicts.pop(0)]
        for target in dicts:
            try:
                similarity = [self.similarity(temp, target) for temp in templates]
                maximum = max(similarity)
                if maximum < 0.75:
                    templates.append(target)
                    continue

                max_index = similarity.index(maximum)
                for key, value in target.items():
                    if key not in templates[max_index].keys() or templates[max_index][key] is None:
                        templates[max_index][key] = value
                    elif isinstance(templates[max_index][key], (dict, list)) and not isinstance(value, (dict, list)):
                        # * dict + str, list + str
                        continue
                    elif isinstance(value, (dict, list)) and not isinstance(templates[max_index][key], (dict, list)):
                        # * str + dict, str + list
                        templates[max_index][key] = value
                    elif isinstance(value, dict):
                        # * template = [dict]
                        if isinstance(templates[max_index][key], list) and [value] == templates[max_index][key]:
                            continue

                        # * [dict] + dict, dict + dict
                        temp = templates[max_index][key] if isinstance(templates[max_index][key], list) else [templates[max_index][key]]
                        temp.append(target[key])
                        templates[max_index][key] = self.__merge_dictionaries(temp)
                    elif isinstance(value, list):
                        if isinstance(templates[max_index][key], list) and templates[max_index][key] == [value]:
                            # * template = [list]
                            continue
                        elif isinstance(templates[max_index][key], list) and [templates[max_index][key]] == value:
                            # * [template] = [list]
                            templates[max_index][key] = value
                            continue

                        # * dict + [dict], dict + [dict, dict], [dict] + [dict]
                        dict_values = [v for v in value if isinstance(v, dict)]
                        if len(dict_values) < 1:
                            templates[max_index][key] = [value]
                        elif len(dict_values) < 2:
                            templates[max_index][key] = [dict_values[0]]
                        else:
                            dict_values.extend(target[key])
                            templates[max_index][key] = self.__merge_dictionaries(dict_values)
                    else:
                        templates[max_index][key] = value
            except:
                print(f"Error: {target}")
        return templates

    def make_template(self, dicts: list = None, save_flag: bool = True, save_json_file: str = "templates.json") -> None | list:
        dicts = self.base if dicts is None else dicts
        dicts = list(dicts) if isinstance(dicts, dict) else dicts if isinstance(dicts, list) else []
        templates = dicts if len(dicts) < 2 else self.__merge_dictionaries(dicts)

        if not save_flag:
            return templates

        with open(save_json_file, "w", encoding="UTF-8") as jf:
            dump(templates, jf, ensure_ascii=False, indent=2)

    def __clear_value_loop(self, dicts: list | dict) -> list:
        if isinstance(dicts, list):
            for idx, d in enumerate(dicts):
                dicts[idx] = self.__clear_value_loop(d)
        elif isinstance(dicts, dict):
            for key, value in dicts.items():
                if isinstance(value, (list, dict)):
                    dicts[key] = self.__clear_value_loop(value)
                else:
                    dicts[key] = None
        return dicts

    def clear_value(self, dicts: list = None, save_flag: bool = True, save_json_file: str = "templates.json") -> None | list:
        dicts = self.base if dicts is None else dicts
        dicts = self.__clear_value_loop(dicts)

        if not save_flag:
            return dicts

        with open(save_json_file, "w", encoding="UTF-8") as jf:
            dump(dicts, jf, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    under_json = Read_Json(address="before.json")
    print(under_json.find_value(target="유리컵"))
    print(under_json.find_value(target="유리컵", related_flag=True))
    print(under_json.find_all(target="라벤더", related_flag=True))
    # print(under_json.make_template())
