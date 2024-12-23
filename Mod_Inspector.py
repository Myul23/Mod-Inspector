from os import path, walk
from glob import glob

from common.json_comfortables import Read_Json
from common.json_matching import JsonMatching
from prior_mod_check import ModChecker


class Mod:
    def __init__(self, unique_id: str = None, priors: list = None, dependencies: dict = None, content: list | dict = None):
        self.id = unique_id  # UniqueID
        self.priors = priors  # ContentPackFor, [dict]
        self.dependencies = dependencies  # dependency
        self.original_content = content

        self.load_file = None
        self.optimized_content = None
        self.manifest = None

    def get_content(self) -> tuple:
        return self.load_file, self.original_content if self.optimized_content is None else self.optimized_content

    def __str__(self):
        return repr(self.get_content())


class ModInspector:
    def __init__(self, address: str, represent_file: str = "manifest.json", total_template_address: str = "cp_templates.json"):
        self.mod_checker = ModChecker()
        self.read_json = Read_Json()
        self.json_matching = JsonMatching()

        self.target_address = address
        self.represent_file = represent_file
        self.total_template = self.read_json.read(total_template_address)
        self.the_number_of_template = self.mod_checker.get_prior_mod_length()
        self.__set_functions_per_prior()
        self.converted_cps = []

    def __set_functions_per_prior(self) -> None:
        self.functions_for_priors = {key: lambda x: x for key in self.mod_checker.get_prior_mod_keys()}

    def __reassemble(self, folder: str) -> None:
        priors = self.mod_checker.check_prior_mod(folder)
        for idx in range(self.the_number_of_template):
            mod = Mod(unique_id=priors[2], priors=priors[0], dependencies={key: [] for key in priors[1]}, content=[])

            # * dependency
            for prior in priors[1]:
                mod.dependencies[prior].extend([mod_id for mod_id in priors[2] if mod_id not in mod.dependencies[prior]])

            # * content pack
            idx = self.the_number_of_template - idx
            if idx not in priors[0]:
                continue

            # * json datas
            for mini_present, _, mini_files in walk(folder):
                if self.represent_file in mini_files:
                    mini_files.remove(self.represent_file)

                for f in mini_files:
                    if not f.endswith(".json"):
                        continue

                    try:
                        data = self.read_json.read(mini_present + "/" + f)
                        mod.original_content = self.read_json.append(mod.original_content, data)
                    except:
                        print(f"{mini_present}/{f} file is failed to load")

            # ? convert per content pack
            func = self.functions_for_priors[self.mod_checker.get_prior_mod_name(idx)]
            print(mod.original_content)
            mod.optimized_content = self.read_json.make_template(
                self.read_json.append(mod.optimized_content, func(mod.original_content), list_flag=True)
            )
            self.converted_cps.append(mod)

    def reconstruct(self) -> list:
        for mod_file in glob(self.target_address + "/*"):
            if not path.isdir(mod_file):
                continue
            print("present mod:", path.split(mod_file)[-1])

            # ? separate per content pack
            for present, _, files in walk(mod_file):
                if self.represent_file not in files:
                    continue
                self.__reassemble(present)
        return self.converted_cps


if __name__ == "__main__":
    # address = "X://0. Stardew Valley Backup/apply"
    address = "X://0. Stardew Valley Backup/0. sample"
    mod_inspector = ModInspector(address=address)

    # print(mod_optimizer.reconstruct)
    for m in mod_inspector.reconstruct():
        print(m)
