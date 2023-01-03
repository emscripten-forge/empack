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


def hotfixes(files):
    for f in files:
        if 'clapack_all.so' in f['filename']:
            f['filename'] = 'clapack_all.so'
    return files

def sort_packed(file_path):
    lines = []
    with open(file_path, "r") as in_file:
        for line in in_file:
            if 'loadPackage({"files":' in line:
                files = json.loads(line[16:-3])["files"]

                files = hotfixes(files)


                files.sort(key=lambda x: x["filename"])
                
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
