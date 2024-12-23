> # Mod Inspector

> Goal: mod -> prior mod check -> transfer -> optimize -> unified mod

- 사전 json read check 필수

<hr style="border-style: dotted; opacity: 0.5;" />

- [json_comfortables.py](common/json_comfortables.py): read, append, find value, find all, extract template in jsons
  - find_all의 경우, 같은 dictionary에선 value searching이 이루어지지 않고 있다.
- [prior_mod_check.py](prior_mod_check.py): json read check, add prior mod list, check the mod's prior mod
