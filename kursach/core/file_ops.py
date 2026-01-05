import os
import shutil
import platform
from datetime import datetime
import mimetypes
import tempfile
import subprocess
import json


def check_file_signature(filepath):

    '''
    Проверка наличия цифровой подписи
    '''

    ps_command = (
        f'Get-AuthenticodeSignature "{filepath}" | '
        f'Select-Object @{{Name="Status"; Expression={{$_.Status.ToString()}}}}, '
        f'@{{Name="SignerCertificate"; Expression={{$_.SignerCertificate.Subject}}}} | '
        f'ConvertTo-Json'
    )

    result = subprocess.run(
        ["powershell", "-Command", ps_command],
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=True
    )

    if not result.stdout.strip():
        return 0

    data = json.loads(result.stdout)

    return f'Статус: {data.get('Status')}, Сертификат: {data.get('SignerCertificate')}'


def open_item(path: str):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
    except Exception as e:
        raise Exception(f"Не удалось открыть {path}: {str(e)}")


def copy_item(src: str, dst_dir: str):
    try:
        base_name = os.path.basename(src)
        dst = os.path.join(dst_dir, base_name)

        src_dir = os.path.dirname(src)
        if src_dir == dst_dir:
            return src

        if os.path.exists(dst):
            name, ext = os.path.splitext(base_name)
            counter = 1
            while os.path.exists(dst):
                dst = os.path.join(dst_dir, f"{name} ({counter}){ext}")
                counter += 1

        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

        return dst
    except Exception as e:
        raise Exception(f"Ошибка при копировании {src}: {str(e)}")


def move_item(src: str, dst_dir: str):
    try:
        dst = os.path.join(dst_dir, os.path.basename(src))

        src_dir = os.path.dirname(src)
        if src_dir == dst_dir:
            return src

        shutil.move(src, dst)
        return dst
    except Exception as e:
        raise Exception(f"Ошибка при перемещении {src}: {str(e)}")


def copy_items(paths: list[str], dst_dir: str):
    for path in paths:
        copy_item(path, dst_dir)


def move_items(paths: list[str], dst_dir: str):
    for path in paths:
        move_item(path, dst_dir)


def delete_item(path: str):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except Exception as e:
        raise Exception(f"Ошибка при удалении {path}: {str(e)}")


def rename_item(path: str, new_name: str):
    try:
        parent = os.path.dirname(path)
        new_path = os.path.join(parent, new_name)
        os.rename(path, new_path)
        return new_path
    except Exception as e:
        raise Exception(f"Ошибка при переименовании {path}: {str(e)}")


def get_properties(path: str) -> dict:
    try:
        stat = os.stat(path)

        sig_result = check_file_signature(path)

        if sig_result:
            signature_info = sig_result
        else:
            signature_info = "Подпись отсутствует"

        return {
            "path": path,
            "type": "Папка" if os.path.isdir(path) else "Файл",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
            "signature": signature_info
        }
    except Exception as e:
        raise Exception(f"Не удалось получить свойства {path}: {str(e)}")


def get_file_preview(path: str):
    try:
        if not os.path.exists(path):
            return "text", "Файл не существует"

        if os.path.isdir(path):
            file_count = 0
            dir_count = 0
            total_size = 0

            for root, dirs, files in os.walk(path):
                dir_count += len(dirs)
                file_count += len(files)
                for file in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, file))
                    except:
                        pass

            text = f"📁 Папка\n\nФайлов: {file_count}\nПапок: {dir_count}\nОбщий размер: {total_size:,} байт"
            return "text", text

        _, ext = os.path.splitext(path.lower())

        if ext in ['.txt', '.py', '.js', '.html', '.css', '.xml', '.json', '.md']:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)
                    return "text", f"📄 Текстовый файл\n\n{content}"
            except:
                return "text", f"📄 Текстовый файл (не удалось прочитать)"

        elif ext == '.docx':
            try:
                import docx
                doc = docx.Document(path)
                text_content = []
                for para in doc.paragraphs[:20]:
                    if para.text.strip():
                        text_content.append(para.text)
                content = "\n".join(text_content)[:2000]
                return "text", f"📝 Документ Word\n\n{content}"
            except:
                return "text", f"📝 Документ Word (не удалось прочитать)"

        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
            try:
                from PIL import Image
                img = Image.open(path)
                width, height = img.size
                size_kb = os.path.getsize(path) // 1024

                preview_size = (300, 300)
                img.thumbnail(preview_size)

                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, f"preview_{os.path.basename(path)}")
                img.save(temp_path, format=img.format if img.format else 'PNG')

                info = f"🖼️ Изображение\n\nРазрешение: {width}x{height}\nРазмер: {size_kb} KB"
                return "image", (temp_path, info)
            except:
                return "text", f"🖼️ Изображение (не удалось открыть)"

        elif ext == '.pdf':
            try:
                import fitz
                doc = fitz.open(path)

                if len(doc) > 0:
                    page = doc[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, f"preview_pdf_{os.path.basename(path)}.png")
                    pix.save(temp_path)

                    info = f"📕 PDF документ\n\nСтраниц: {len(doc)}\nРазмер: {os.path.getsize(path) // 1024} KB"
                    return "image", (temp_path, info)
                else:
                    return "text", "📕 PDF документ (пустой)"
            except:
                return "text", f"📕 PDF документ (не удалось открыть)"

        else:
            mime_type, _ = mimetypes.guess_type(path)
            size = os.path.getsize(path)

            if ext in ['.exe', '.dll', '.sys', '.msi']:
                sig_result = check_file_signature(path)
                return "text", f"📎 Исполняемый файл\n\nТип: {mime_type or 'неизвестный'}\nРазмер: {size:,} байт\nПодпись: {sig_result}"

            return "text", f"📎 Файл\n\nТип: {mime_type or 'неизвестный'}\nРазмер: {size:,} байт"

    except Exception as e:
        return "text", f"Ошибка при предпросмотре: {str(e)}"
