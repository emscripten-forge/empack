import json


def extend_logging(file_path):
    lines = []
    with open(file_path, "r") as in_file:
        for line in in_file:
            if (
                """if (Module['setStatus']) Module['setStatus']('Downloading data... (' + loaded + '/' + total + ')');"""  # noqa: E501
                in line
            ):

                lines.append(
                    """            if (Module['empackSetStatus']) Module['empackSetStatus']('Downloading',PACKAGE_NAME,loaded,total);\n"""  # noqa: E501
                )
            lines.append(line)
    with open(file_path, "wt") as out_file:
        for line in lines:
            out_file.write(line)


def sort_packed(file_path):
    lines = []
    with open(file_path, "r") as in_file:
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
    with open(file_path, "wt") as out_file:
        for line in lines:
            out_file.write(line)


def extend_js(file_path):
    sort_packed(file_path)
    extend_logging(file_path)
