from os import walk, path
from json import dump
from json.decoder import JSONDecodeError
from jstyleson import load


class ModChecker:
    def __init__(self, prior_mods_address: str = "prior_mods.json"):
        with open(prior_mods_address, "r") as jf:
            self.__prior_mods = load(jf)
        self.__prior_mods_number = len(self.__prior_mods.keys())
        self.represent_file = "manifest.json"

    def get_prior_mod_name(self, number: int) -> str:
        return list(self.__prior_mods.keys())[number]

    def get_prior_mod_keys(self) -> dict:
        return self.__prior_mods.keys()

    def get_prior_mod_length(self) -> int:
        return self.__prior_mods_number

    def __check_read(file_path: str) -> bool:
        try:
            with open(file_path, "r", encoding="UTF-8-SIG") as jf:
                load(jf)
            return True
        except JSONDecodeError:
            path.startfile(file_path)
        except:
            print(file_path)
        finally:
            return False

    def check_read(self, address: str, prior_flag: bool = True) -> bool:
        if address is None or not path.isabs(address):
            print("Please check that input path is not None and is absolute path")
            return False

        if prior_flag:
            for present, _, files in walk(address):
                if not self.represent_file in files:
                    return False
                return self.__check_read(present + "/" + self.represent_file)
        else:
            for present, _, files in walk(address):
                for f in files:
                    if not f.endswith(".json"):
                        continue
                    return self.__check_read(present + "/" + f)

    def add_prior_list(self, address: str, visualization: bool = False) -> None:
        for present, _, files in walk(address):
            if not self.represent_file in files:
                continue

            try:
                with open(present + "/" + self.represent_file, "r", encoding="UTF-8-SIG") as manifest:
                    prior = load(manifest).get("ContentPackFor")
                if prior is None or prior["UniqueID"] in self.__prior_mods.keys():
                    continue
                self.__prior_mods[prior["UniqueID"]] = self.__prior_mods_number
                self.__prior_mods_number += 1
            except JSONDecodeError as e:
                print(e)
                print(f"That file is {present}/{self.represent_file}")
                break

        if visualization:
            for key in self.__prior_mods.keys():
                print(key, end=" | ")
            return

        with open("prior_mods.json", "w") as jf:
            dump(self.__prior_mods, jf)

    def check_prior_mod(self, address: str) -> tuple:
        contentpacks, dependencies, mod_ids = [], [], []
        for present, _, files in walk(address):
            if not self.represent_file in files:
                continue

            try:
                with open(present + "/" + self.represent_file, "r", encoding="UTF-8-SIG") as manifest:
                    data = load(manifest)
                mod_id = data.get("UniqueID")
                if mod_id is not None:
                    mod_ids.append(mod_id)

                contentpack = data.get("ContentPackFor")
                if contentpack is not None and contentpack["UniqueID"] in self.__prior_mods.keys():
                    contentpacks.append(self.__prior_mods[contentpack["UniqueID"]])

                dependency = data.get("Dependencies")
                if dependency is None:
                    continue
                dependencies.extend([d["UniqueID"] for d in dependency])
            except JSONDecodeError as e:
                print(e)
                print(f"That file is {present}/{self.represent_file}")
                break
        return list(set(contentpacks)), list(set(dependencies)), list(set(mod_ids))


if __name__ == "__main__":
    address = "X://0. Stardew Valley Backup/apply"
    mod_checker = ModChecker()
    mod_checker.check_read(address, prior_flag=True)
    mod_checker.check_read(address, prior_flag=False)
    # prior.add_prior_list(address, visualization=True)
    # print(prior.check_prior_mod(address))
