import json
import copy
from collections import defaultdict
import subprocess

# remove items not strictly needed to do the package solving (things like licenses)
# from the pkg meta dict
def shrink_pkg_meta(pkg_meta):
    to_keep = ["name", "version", "build", "depends", "build_number"]
    return {key: pkg_meta[key] for key in to_keep}


# remove items not strictly needed to do the package solving (things like licenses)
def shrink_pkg_meta_items(repodata):
    shrinked_repodata = copy.deepcopy(repodata)

    shrinked_packages = {}
    for pkg_key, pkg_meta in repodata["packages"].items():
        shrinked_pkg_meta = shrink_pkg_meta(pkg_meta)
        shrinked_packages[pkg_key] = shrinked_pkg_meta
    shrinked_repodata["packages"] = shrinked_packages
    return shrinked_repodata


# filter out norach pkg which need some non-available arch pkg
def shrink_trivial_unsatisfiable(noarch_repodata, *args):
    shrinked_noarch_repodata = copy.deepcopy(noarch_repodata)

    repodatas = [noarch_repodata] + list(args)

    pkg_names = set()
    for repodata in repodatas:
        for pkg_meta in repodata["packages"].values():
            pkg_names.add(pkg_meta["name"])

    shrinked_packages = {}
    for package_key, pkg_meta in noarch_repodata["packages"].items():
        deps = pkg_meta["depends"]

        is_satisfiable = True
        for dep_str in deps:
            dep_name = dep_str.split(" ")[0]
            if dep_name not in pkg_names:
                is_satisfiable = False
                # print(f"skip {package_key} unsatisfiable dep: {dep_name}")
                break

        if is_satisfiable:
            shrinked_packages[package_key] = pkg_meta

    shrinked_noarch_repodata["packages"] = shrinked_packages

    return shrinked_noarch_repodata


# only keep latest build number
def only_keep_latest_build_number(repodata):
    shrinked_repodata = copy.deepcopy(repodata)

    # outer dict groups pkgs by name, the value type
    # is another dict:
    # The inner dict key is the version number
    # the value is a list of builds which have that version
    # (ie the different build numbers)
    named_grouped_pkgs = defaultdict(lambda: defaultdict(lambda: []))
    for package_key, pkg_meta in repodata["packages"].items():
        name = pkg_meta["name"]
        version = pkg_meta["version"]
        pkg_meta["_packages_key"] = package_key
        named_grouped_pkgs[name][version].append(pkg_meta)

    shrinked_packages = {}

    # i = 0
    for pkg_name, versions in named_grouped_pkgs.items():

        # print(pkg_name)

        # interate over all versions for that given pkg
        for version, pkgs in versions.items():

            # highest build number only
            pkg_meta = max(pkgs, key=lambda pkg_meta: int(pkg_meta["build_number"]))
            package_key = pkg_meta.pop("_packages_key")
            shrinked_packages[package_key] = pkg_meta

        # i += 1
        # if i > 10:
        #     break
    shrinked_repodata["packages"] = shrinked_packages
    return shrinked_repodata


# filter out norach pkg which need some non-available arch pkg
def filter_out_explict_unsat_deps(noarch_repodata):
    shrinked_noarch_repodata = copy.deepcopy(noarch_repodata)

    prohibited_content = [
        "python >=3.6,<3.9",
        "python <3.7",
        "python <3.6",
        "javapackages-tools",
        "sysroot_linux",
        "cos7",
    ]

    shrinked_packages = {}
    for package_key, pkg_meta in noarch_repodata["packages"].items():
        deps = pkg_meta["depends"]

        is_satisfiable = True
        for dep_str in deps:
            if is_satisfiable:
                for ph in prohibited_content:
                    if ph in dep_str:
                        is_satisfiable = False
                        print("skip", package_key)
                        break

        if is_satisfiable:
            shrinked_packages[package_key] = pkg_meta

    shrinked_noarch_repodata["packages"] = shrinked_packages

    return shrinked_noarch_repodata


# filter out by name
def filter_out_by_pkg_name(noarch_repodata):
    shrinked_noarch_repodata = copy.deepcopy(noarch_repodata)

    prohibited_content = [
        "javapackages-tools",
        "openjdk",
        "libgfortran-devel",
        "cos7",
        "napari",
        "conda-forge-pinning-",
        "conda-forge-repodata-patches-",
        "conda-lock-",
        "ensureconda",
        "kernel-headers",
    ]

    shrinked_packages = {}
    for package_key, pkg_meta in noarch_repodata["packages"].items():

        use = True
        for ph in prohibited_content:
            if ph in package_key:
                use = False
                print("skip by name", package_key)
                break

        if use:
            shrinked_packages[package_key] = pkg_meta

    shrinked_noarch_repodata["packages"] = shrinked_packages

    return shrinked_noarch_repodata


def filter_out_by_micromamba(noarch_repodata):
    import tempfile

    shrinked_noarch_repodata = copy.deepcopy(noarch_repodata)

    done = set()

    shrinked_packages = {}
    for package_key, pkg_meta in noarch_repodata["packages"].items():

        if pkg_meta["name"] in done:
            continue
        done.add(pkg_meta["name"])

        with tempfile.TemporaryDirectory() as prefix:
            use = True
            args = f"""/home/derthorsten/miniconda3/bin/micromamba create --prefix {str(prefix)} --platform=emscripten-32 \
                -c https://repo.mamba.pm/emscripten-forge \
                -c https://repo.mamba.pm/conda-forge \
                --yes \
                --dry-run \
                {pkg_meta["name"]}
            """
            # args = args.split(" ")
            args = [args]
            r = subprocess.run(
                args, shell=True
            )  # stderr=subprocess.STDOUT, stdout=subprocess.STDOUT)

            if r.returncode != 0:
                use = False
                print(r.returncode, r)
                print(f"skip {package_key}")

            if use:
                shrinked_packages[package_key] = pkg_meta

    shrinked_noarch_repodata["packages"] = shrinked_packages

    return shrinked_noarch_repodata


# if __name__ == "__main__":
#     noarch_in = "conda_forge_noarch_repodata.json"
#     em_32_in = "emscripten_forge_emscripten_32_repodata.json"
#     noarch_out = "shrinked_conda_forge_noarch_repodata.json"

#     with open(noarch_in, "r") as f_in:
#         noarch_repodata = json.load(f_in)

#     with open(em_32_in, "r") as f_in:
#         em_32_repodata = json.load(f_in)

#     shrinked_noarch_repodata = noarch_repodata
#     shrinked_noarch_repodata = filter_out_by_pkg_name(shrinked_noarch_repodata)
#     shrinked_noarch_repodata = shrink_pkg_meta_items(shrinked_noarch_repodata)
#     shrinked_noarch_repodata = only_keep_latest_build_number(shrinked_noarch_repodata)
#     shrinked_noarch_repodata = shrink_trivial_unsatisfiable(
#         shrinked_noarch_repodata, em_32_repodata
#     )
#     shrinked_noarch_repodata = filter_out_explict_unsat_deps(shrinked_noarch_repodata)
#     # shrinked_noarch_repodata = filter_out_by_micromamba(shrinked_noarch_repodata)
#     with open(noarch_out, "w") as f_out:
#         # repodata = json.dump(shrinked_noarch_repodata, f_out, indent=4)
#         repodata = json.dump(shrinked_noarch_repodata, f_out)
