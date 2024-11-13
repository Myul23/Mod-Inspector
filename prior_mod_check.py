import os, json, jstyleson


class PriorMod:
    def __init__(self, prior_mods_address: str = "prior_mods.json"):
        with open(prior_mods_address, "r") as jf:
            self.prior_mods = json.load(jf)
        self.__prior_mods_number = len(self.prior_mods.keys())

    def read_check(self, address: str) -> None:
        for present, _, files in os.walk(address):
            for f in files:
                if ".json" not in f:
                    continue
                try:
                    with open(present + "/" + f, "r", encoding="UTF-8-SIG") as jf:
                        jstyleson.load(jf)
                except json.decoder.JSONDecodeError:
                    os.startfile(f"{present}/{f}")
                    exit(1)

    def prior_read_check(self, address: str) -> None:
        for present, _, files in os.walk(address):
            if not "manifest.json" in files:
                continue
            try:
                with open(present + "/manifest.json", "r", encoding="UTF-8-SIG") as manifest:
                    jstyleson.load(manifest)
            except json.decoder.JSONDecodeError:
                os.startfile(f"{present}/manifest.json")

    def prior_list_add(self, address: str, visualization: bool = False) -> None:
        for present, _, files in os.walk(address):
            if not "manifest.json" in files:
                continue

            try:
                with open(present + "/manifest.json", "r", encoding="UTF-8-SIG") as manifest:
                    prior = jstyleson.load(manifest).get("ContentPackFor")
                if prior is None or prior["UniqueID"] in self.prior_mods.keys():
                    continue
                self.prior_mods[prior["UniqueID"]] = self.__prior_mods_number
                self.__prior_mods_number += 1
            except json.decoder.JSONDecodeError as e:
                print(e)
                print(f"That file is {present}/manifest.json")
                break

        if visualization:
            for key in self.prior_mods.keys():
                print(key, end=" | ")
            return

        with open("prior_mods.json", "w") as jf:
            json.dump(self.prior_mods, jf)

    def prior_mod_check(self, address: str) -> tuple:
        contentpacks, dependencies = [], []
        for present, _, files in os.walk(address):
            if not "manifest.json" in files:
                continue

            try:
                with open(present + "/manifest.json", "r", encoding="UTF-8-SIG") as manifest:
                    data = jstyleson.load(manifest)
                contentpack = data.get("ContentPackFor")
                if contentpack is not None and contentpack["UniqueID"] in self.prior_mods.keys():
                    contentpacks.append(contentpack["UniqueID"])

                dependency = data.get("Dependencies")
                if dependency is None:
                    continue
                for d in dependency:
                    dependencies.append(d["UniqueID"])
            except json.decoder.JSONDecodeError as e:
                print(e)
                print(f"That file is {present}/manifest.json")
                break
        return list(set(contentpacks)), list(set(dependencies))


if __name__ == "__main__":
    address = "apply"
    prior = PriorMod()
    prior.read_check(address)
    # prior.prior_read_check(address)
    # prior.prior_list_add(address, visualization=True)
    # print(prior.prior_mod_check(address))
