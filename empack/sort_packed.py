import json


def sort_packed(in_file_path, out_file_path):
    lines = []
    with open(in_file_path, "r") as in_file:
        for line in in_file:
            if 'loadPackage({"files":' in line:
                files = json.loads(line[16:-3])["files"]
                files.sort(key=lambda x: x["filename"])
                # for file in files:
                #     print(file)
                line = f"""loadPackage({
                    json.dumps({"files": files})
                });"""
            lines.append(line)
    with open(out_file_path, "wt") as out_file:
        for line in lines:
            out_file.write(line)
