import shutil
import os


def copy_file(src, dst):

    """Копирование файла"""

    shutil.copy2(src, dst)


def move_file(src, dst):

    """Перемещение файла"""

    shutil.move(src, dst)


def delete_file(path):

    """Удаление файла или каталога"""

    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
