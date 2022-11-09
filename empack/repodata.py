import requests
import bz2
import io
import json
from pathlib import Path
import os


def get_pkg_names(repodata):
    pkg_names = set()
    for k, v in repodata.items():
        for pkg_key, meta in v["packages"].items():
            pkg_names.add(meta["name"])
    # print("#",len(pkg_names))
    return pkg_names


def pkg_name_from_dependency_str(s):
    if " " in s:
        return s.split(" ")[0]
    else:
        return s


def remove_non_available(repodata):

    noarch_pkgs = repodata["noarch"]["packages"]

    i = 0
    while True:
        pkg_names = get_pkg_names(repodata)
        removed_one = False
        i += 1
        for pkg_key in list(noarch_pkgs.keys()):
            meta = noarch_pkgs[pkg_key]
            depends = meta["depends"]
            for d in depends:
                d_pkg_name = pkg_name_from_dependency_str(d)
                if d_pkg_name not in pkg_names:
                    del noarch_pkgs[pkg_key]
                    removed_one = True
                    break
        if not removed_one:
            break


def hack_fields(repodata):
    for k, v in repodata.items():
        for pkg_key, meta in v["packages"].items():

            # fmt: off

            meta['md5'] = "00000000000000000000000000000000"
            meta['sha256'] = "0000000000000000000000000000000000000000000000000000000000000000"
            meta['size'] = 1
            meta['timestamp'] = 1
            meta['time_modified'] = 1
            # fmt: on


def download_and_shrink_repodata(repodata_urls, outdir=None):
    if outdir is None:
        outdir = os.getcwd()
    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True, parents=True)

    if "arch" not in repodata_urls or "noarch" not in repodata_urls:
        raise RuntimeError("need'arch' / 'noarch' keys in repodata_urls")

    # print("download")
    # download
    repodata_urls[
        "arch"
    ] = "https://beta.mamba.pm/get/emscripten-forge/emscripten-32/repodata.json.bz2"

    repodata_urls[
        "noarch"
    ] = "https://beta.mamba.pm/get/conda-forge/noarch/repodata.json.bz2"
    repodata_response = {k: requests.get(url) for k, url in repodata_urls.items()}
    [r.raise_for_status() for r in repodata_response.values()]

    # unzip
    repodata = dict()
    for k, response in repodata_response.items():
        with bz2.BZ2File(io.BytesIO(response.content)) as f:
            repodata[k] = json.load(f)

            with open(outdir / f"{k}_repodata.json", "w") as fp:
                json.dump(repodata[k], fp, indent=4)

    # print("pre", len(repodata["noarch"]["packages"]))
    remove_non_available(repodata)
    # print("post", len(repodata["noarch"]["packages"]))

    hack_fields(repodata)
    # wripte bz2
    for k, v in repodata.items():
        with open(outdir / f"{k}_shrinked_repodata.json", "w") as fp:
            json.dump(v, fp, indent=4)
        tarbz2contents = bz2.compress(json.dumps(v).encode(), 9)
        with open(outdir / f"{k}_picomamba.bz2", "wb") as f:
            f.write(tarbz2contents)


if __name__ == "__main__":

    repodata_urls = {
        "arch": "https://beta.mamba.pm/get/emscripten-forge/emscripten-32/repodata.json.bz2",
        "noarch": "https://beta.mamba.pm/get/conda-forge/noarch/repodata.json.bz2",
    }

    download_and_shrink_repodata(repodata_urls)
