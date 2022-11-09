import picomamba


def callback(name, done, total):
    percent = 100.0 * done / total
    print(f"{name} {percent:.2f}% ({done}/{total})")


async def main():

    port = 8000
    dist_url = f"http://127.0.0.1:{port}"
    env_prefix = "/home/web_user/picomamba/env"
    repodata_dir = "/home/web_user"

    arch_root_url = f"{dist_url}"

    arch_repodata_url = f"{dist_url}/arch_repodata_picomamba.tar.bz2"
    noarch_repodata_url = f"{dist_url}/noarch_repodata_picomamba.tar.bz2"

    noarch_template = (
        "https://beta.mamba.pm/get/conda-forge/noarch/{name}-{version}-{build}.tar.bz2"
    )
    pm = picomamba.PicoMamba(
        env_prefix=env_prefix,  # the name of the env
        repodata_dir=repodata_dir,  # where to store repodata
        arch_root_url=arch_root_url,  # root url for arch pkgs
        noarch_template=noarch_template,  # templated url for norach pkgs
        progress_callback=callback,  # report download progress
    )
    await pm.fetch_repodata(
        arch_url=arch_repodata_url,  # url for arch repodata tar.bz2 file
        noarch_url=noarch_repodata_url,  # url for noarch repodata tar.bz2 file
    )
    transaction = pm.solve(["regex"])
    await pm.install_transaction(transaction)

    import regex
