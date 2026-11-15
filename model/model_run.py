#!/usr/bin/env python3
from pathlib import Path

from payload.parser import parse
from payload import finish

import re
import itertools

import numpy as np

TRANSFORM_TYPE = [2,2,2,1,2,2,2,1,2,2,2,1,0,0,0,0]

class BlockDisplayCMD:
    def __init__(self, raw, tol):
        self.raw = raw
        vals_str = re.search(r"(?<=\[).*?(?=\])", self.raw).group()
        self.transformation = [float(val.rstrip('f')) for val in vals_str.split(',')]
        self.tolerances = self.get_tolerances(tol[0], tol[1])
        self.errors = [LossyNumber(self.transformation[i], self.tolerances[self.num_type(i)]) for i in range(len(self.transformation))]

    def get_tolerances(self, e, r):
        L = np.linalg.norm(np.array(self.transformation).reshape(4,4)[:3, :3], axis=0)
        rot_error = np.minimum(e, np.maximum(r * L, 1e-4))
        transform_error = max(1e-4, min(e / 2, 0.25 * L.min()))
        return [0, float(transform_error)] + rot_error.tolist()

    def num_type(self, i):
        """
        if i >= 12: return 0
        elif (i + 1) % 4 == 0: return 1
        else: return ((i + 1) % 4) + 1
        """
        return TRANSFORM_TYPE[i]

    def __str__(self):
        return re.sub(r"(?<=\[).*?(?=\])", ",".join(map(str, self.errors)), self.raw)

    def __iter__(self):
        for num in self.errors:
            yield num

class LossyNumber:
    def __init__(self, num, e):
        self.num = num
        self.min = num - e
        self.max = num + e
        self.decided = None

    def __lt__(self, other):
        return self.min < other.min

    def __str__(self):
        s = str(round_in_range(self.decided[0], self.min, self.max))
        return ("0" if s in ("", "-0") else s)

    def __repr__(self):
        return self.__str__()

def round_in_range(num, min, max):
    nd = 10
    new = 0
    while True:
        if nd == 0:
            break
        new = round(num, nd)
        if new >= min and new <= max: nd = nd - 1
        else: break
    return round(num, nd + 1)

def get_passengers(cmds):
    tolerances = (0.015, 0.5 * np.pi / 180) # 0.015 blocks deviation, 0.5 degrees deviation. Hardcoded, can be automatically determined
    displays = []
    for cmd in cmds:
        for display in re.finditer(r"{id.*?]}", cmd):
            displays.append(BlockDisplayCMD(display.group(0), tolerances))

    errors = list(itertools.chain.from_iterable(displays))
    errors.sort()
    current_decision = [None]
    current_min = errors[0].min
    current_max = errors[0].max
    for i in range(len(errors)):
        iter_min = errors[i].min
        iter_max = errors[i].max
        if not (iter_max < current_min or iter_min > current_max):
            errors[i].decided = current_decision
            current_min = iter_min
            if iter_max < current_max:
                current_max = iter_max
        else:
            current_decision[0] = (current_min + current_max) / 2
            current_decision = [None]
            current_min = iter_min
            current_max = iter_max
            errors[i].decided = current_decision
    current_decision[0] = (current_min + current_max) / 2
    return displays

def file_lines(file_path):
    file = open(file_path)
    file_lines = []
    for line in file:
        new = line.strip()
        if len(new) > 0 and new[0] != "#":
            file_lines.append(new)
    file.close()
    return file_lines

def split_summons(block_displays):
    template = file_lines(Path("model/minecart_template.mcfunction"))
    
    all_minecarts = []
    current = ""
    add = lambda new: all_minecarts.append(parse.parse_command(template, [parse.get_parse_raw_data({"passengers":f"[{new[:-1]}]"})])[0])
    for display in block_displays:
        display = str(display)
        new = current + display + ","
        if len(new) >= (32500 - 103 - 2):
            add(current)
            current = display + ","
            continue
        current = new
    add(current)
    return all_minecarts

def main():
    raw_path = Path("model/block-display/exported.txt")
    raw_lines = file_lines(raw_path)
    display_minecarts = split_summons(get_passengers(raw_lines))
    command = Path("model/summon.mcfunction")
    final_command_lines = parse.parse_command(file_lines(command), [parse.get_parse_raw_data({"summons":("".join(display_minecarts))})])
    print(f"Length of original raw commands: {sum(map(len, raw_lines))}")
    print(f"Length of raw model to be pasted: {sum(map(len, display_minecarts))}")
    finish.finish("".join(final_command_lines), ("clipboard","write"), "model/model_payload.txt")

if __name__ == "__main__":
    main()
