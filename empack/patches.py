
def clapack_hotfix(files):
    for f in files:
        if 'clapack_all.so' in f['filename']:
            f['filename'] = 'clapack_all.so'


    return files

def scipy_hotfix(files):
    """
        hotfix to **NOT** use the alphabetic order
        
        This is to get rid of this error:

        Couldn't instantiate wasm: /prefix/lib/python3.10/site-packages/scipy/sparse/linalg/_propack/_cpropack.cpython-310-wasm32-emscripten.so 'Error: bad export type for `bbcom_`: undefined'
        Couldn't instantiate wasm: /prefix/lib/python3.10/site-packages/scipy/sparse/linalg/_propack/_dpropack.cpython-310-wasm32-emscripten.so 'Error: bad export type for `bbcom_`: undefined'
        Couldn't instantiate wasm: /prefix/lib/python3.10/site-packages/scipy/sparse/linalg/_propack/_spropack.cpython-310-wasm32-emscripten.so 'Error: bad export type for `bbcom_`: undefined'

        Good order:

        {"filename": "_spropack.cpython-310-wasm32-emscripten.so", "start": 26414466, "end": 26592339}, 
        {"filename": "_dpropack.cpython-310-wasm32-emscripten.so", "start": 26236357, "end": 26414466}, 
        {"filename": "_zpropack.cpython-310-wasm32-emscripten.so", "start": 26592339, "end": 27039670}, 
        {"filename": "_cpropack.cpython-310-wasm32-emscripten.so", "start": 26011033, "end": 26236357}, 


        Baaad order:

        {"filename": "_cpropack.cpython-310-wasm32-emscripten.so", "start": 26011033, "end": 26236357}, 
        {"filename": "_dpropack.cpython-310-wasm32-emscripten.so", "start": 26236357, "end": 26414466}, 
        {"filename": "_spropack.cpython-310-wasm32-emscripten.so", "start": 26414466, "end": 26592339}, 
        {"filename": "_zpropack.cpython-310-wasm32-emscripten.so", "start": 26592339, "end": 27039670}, 


        """
    has_cpropack_file = False
    for i, f in enumerate(files):
        if "_cpropack.cpython-310-wasm32-emscripten.so" in str(f):
           has_cpropack_file = True
           propack_index = i
           break
    if not has_cpropack_file: 
        return files

    new_files = list(files[0:propack_index])
    new_files.append(files[propack_index+2]) # s-propack
    new_files.append(files[propack_index+1]) # d-propack
    new_files.append(files[propack_index+3]) # z-propack
    new_files.append(files[propack_index+0]) # c-propack
    new_files.extend(files[propack_index+4:])
    return new_files
