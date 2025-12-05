import os
import shutil
from datetime import datetime


def get_properties(path: str) -> dict:
    info = os.stat(path)
    return {
        "path": path,
        "is_dir": os.path.isdir(path),
        "size": info.st_size,
        "modified": datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    }


def rename_item(old_path: str, new_name: str) -> str:
    base_dir = os.path.dirname(old_path)
    new_path = os.path.join(base_dir, new_name)
    os.rename(old_path, new_path)
    return new_path


def copy_item(src: str, dst_dir: str) -> str:
    name = os.path.basename(src)
    dst_path = os.path.join(dst_dir, name)

    if os.path.exists(dst_path):
        dst_path = dst_path + "_copy"

    if os.path.isdir(src):
        shutil.copytree(src, dst_path)
    else:
        shutil.copy2(src, dst_path)

    return dst_path


def delete_item(path: str):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def create_folder(parent_dir: str, folder_name: str) -> str:
    if not os.path.isdir(parent_dir):
        raise NotADirectoryError(parent_dir)

    new_path = os.path.join(parent_dir, folder_name)
    counter = 1
    base_new_path = new_path
    while os.path.exists(new_path):
        new_path = f"{base_new_path}_{counter}"
        counter += 1

    os.makedirs(new_path, exist_ok=True)
    return new_path


def normalize(path: str) -> str:
    return os.path.abspath(path).replace("\\", "/")
