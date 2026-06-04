import os
import sys

_RUNTIME_READY = False


def ensure_clr_loaded():
    global _RUNTIME_READY

    if not _RUNTIME_READY:
        from pythonnet import load

        runtime = "mono" if sys.platform.startswith("linux") else "coreclr"
        load(runtime)
        _RUNTIME_READY = True

    import clr

    clr.AddReference("System")
    from System.Collections.Generic import List

    return clr, List


def load_pbe_apis(current_file):
    clr, _ = ensure_clr_loaded()

    parent_dir = os.path.dirname(os.path.abspath(current_file))
    dll_dir = os.path.join(parent_dir, "PythonDemo_AutoRelate", "dlls")

    if dll_dir not in sys.path:
        sys.path.append(dll_dir)

    dlls = sorted(
        f
        for f in os.listdir(dll_dir)
        if os.path.isfile(os.path.join(dll_dir, f)) and f.endswith(".dll")
    )
    for dll in dlls:
        clr.AddReference(dll.rsplit(".", 1)[0])

    import PBESynthesis as PBESynthesis

    pbe_file_api = PBESynthesis.PBESynthesisAndHT_Run_One_CSV()
    pbe_row_api = PBESynthesis.PBESynthesisAndHT()
    return pbe_file_api, pbe_row_api, len(dlls)
