import os
from pathlib import Path

this_dir = Path(os.path.dirname(os.path.realpath(__file__)))

dist_dir = this_dir / "outdir" / "distribution"

bucket_name = "picomamba-gra-emscripten-forge"

s3_path = bucket_name


def upload_directory(client, path, bucketname):
    for root, dirs, files in os.walk(path):
        for file in files:
            mimetype = None
            if str(file).endswith(".js"):
                mimetype = "text/javascript"
            elif str(file).endswith(".json"):
                mimetype = "application/json"
            elif str(file).endswith(".wasm"):
                mimetype = "application/wasm"
            print(f"uploading {file}")

            kwargs = {}
            if mimetype is not None:
                kwargs["ExtraArgs"] = {"ContentType": mimetype}
            s3.upload_file(os.path.join(root, file), bucketname, file, **kwargs)


import boto3

s3 = boto3.client(
    "s3", region_name="GRA", endpoint_url="https://storage.gra.cloud.ovh.net"
)


upload_directory(client=s3, path=dist_dir, bucketname="picomamba-gra-emscripten-forge")
