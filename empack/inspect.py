from pathlib import Path
import json


def inspect_packed(js_file: Path):
    with open(js_file, "r") as f:
        for line in f.readlines():
            start = 'loadPackage({"files": ['
            crop_from_start = len("loadPackage(")
            if line.startswith(start):
                content = line[crop_from_start:-3]
                content = json.loads(content)
                break

    # sort by filesize
    def get_size(d):
        return d["end"] - d["start"]

    sorted_files = sorted(content["files"], key=get_size, reverse=True)

    for d in sorted_files:
        filename = d["filename"]
        s = get_size(d)

        print(f"{s:<10} {filename:<10} ")
