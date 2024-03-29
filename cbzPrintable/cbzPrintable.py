import os
import sys
import glob
import argparse
import contextlib
import shutil
from time import sleep
import copy
from math import floor
from PIL import Image, ImageOps
import numpy as np
import PyPDF2
import re
from cbzPrintable.__init__ import VERSION

print(f"using cbzPrintable {VERSION}")

explain = {}


def check_for_error(errors, func):
    if len(errors) == 0:
        return
    if isinstance(errors, dict):
        max_overflow = 15
        for error, data in errors.items():
            if len(data) > max_overflow:
                print(
                    f"ERROR: {func.__name__} failed with return code {error}; {data[:max_overflow]} ..."
                )
            else:
                print(f"ERROR: {func.__name__} failed with return code {error}; {data}")
    else:
        for error in errors:
            print(f"ERROR: {func.__name__} failed with return code {error}")

    print(f"\nTry adding '--explain {min(errors)}' to see the error code")


def ErrorWrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return_code = func(*args, **kwargs)
            if return_code == 0:
                sys.exit(0)
            elif return_code is None:
                print(f"WARNING: {func.__name__} should return 0")
            elif isinstance(return_code, str):
                print(f"WARNING: {func.__name__} should not return a string but 0")
            elif isinstance(return_code, bool):
                print(f"WARNING: {func.__name__} should not return a bool but 0")
            elif isinstance(return_code, float):
                print(f"WARNING: {func.__name__} should not return a float but 0")
            elif isinstance(return_code, (list, tuple, set, dict)):
                check_for_error(return_code, func)
            elif isinstance(return_code, bytes):
                print(f"WARNING: {func.__name__} should not return a bytes but 0")
            elif isinstance(return_code, bytearray):
                print(f"WARNING: {func.__name__} should not return a bytearray but 0")
            elif return_code == 1 and isinstance(return_code, int):
                print(f"ERROR: {func.__name__} failed with return code {return_code}")
            elif return_code != 0 and isinstance(return_code, int):
                print(
                    f"ERROR: {func.__name__} failed with return code {return_code}\n\nTry adding '--explain {return_code}' to see the error code"
                )
                sys.exit(return_code)
            else:
                print(
                    "WARNING: "
                    + func.__name__
                    + f" should return 0, not {type(return_code)}"
                )
        except Exception as e:
            print(e)
            return 1

    return wrapper


def sort_func(input_file):
    if args.file_pattern is not None:
        return float(
            input_file.split(args.file_pattern.split("*")[0])[1].split(
                args.file_pattern.split("*")[1]
            )[0]
        )
    input_file = input_file.split("\\")[1].rsplit(".", 1)[0]
    pattern = re.compile(
        "^(((V|v)(O|o)(L|l)\.)[0-9]+ (C|c)(H|h).[0-9]+)|((C|c)(H|h).[0-9]+)|((C|c)(H|h)(A|a)(P|p)(T|t)(E|e)(R|r) [0-9]+)$"
    )
    pos = pattern.search(input_file)
    input_file = input_file[pos.regs[0][0] : pos.regs[0][1]]
    number = -1
    while True:
        try:
            a = input_file[number:]
            if a[0] == ".":
                number -= 1
                continue
            value = float(input_file[number:])
            number -= 1
        except ValueError:
            break
    return value


def sort_func1(input_file):
    input_file = input_file.split("\\")[-1]
    input_file = int(input_file.split(".")[0])
    return input_file


@ErrorWrapper
def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--explain",
        type=int,
        help="explain error code",
        choices=explain.keys(),
        metavar="ERROR_CODE",
        default=None,
    )
    parser.add_argument("input", help="input folder")
    parser.add_argument(
        "-fp", "--file_pattern", help="file pattern same as glob pattern"
    )
    args = parser.parse_args()

    if args.explain is not None:
        print(f"EXPLAIN: Explaining error code: {args.explain}")
        print(f" EXPLAIN:  {explain[args.explain]}")
        return 0
    try:
        import CbxManager
    except ImportError:
        os.system("git clone https://github.com/Lightjohn/CbXManager.git")
        os.system(sys.executable + " -m pip install -r CbXManager\\requirements.txt")
        os.system(sys.executable + " -m pip install CbXManager\\")
        import CbxManager
    times = 0
    files = glob.glob(f"{args.input}\*.cbz")
    files.sort(key=sort_func)
    files_temp = copy.deepcopy(files)
    volume = 1
    for file in files:
        os.makedirs("temp", exist_ok=True)
        if times == 0:
            for i in range(10):
                try:
                    print(f"{str(i + 1)}) {files_temp[i]}")
                except IndexError:
                    break
            vstup = input("Select HOW MANY IN A ROW volumes to pack > ")
            if vstup == "*" or int(vstup) > len(files_temp):
                vstup = len(files_temp)
            else:
                vstup = int(vstup)
            number = 1
            times = vstup
        CbxManager.CbxManager().parse_cbz(file)
        pattern = re.compile(
            "^(((V|v)(O|o)(L|l)\.)[0-9]+ (C|c)(H|h).[0-9]+)|((C|c)(H|h).[0-9]+)|((C|c)(H|h)(A|a)(P|p)(T|t)(E|e)(R|r) [0-9]+)$"
        )
        pos = pattern.search(file)
        file_new = (
            file.rsplit("\\", 1)[0] + "\\" + file[pos.regs[0][0] : pos.regs[0][1]]
        )
        file_old = file.rsplit(".", 1)[0]
        os.rename(file_old + "\\", file_new + "\\")
        filename = file_new
        print(f"{filename}\\*.jpg")
        image_files = glob.glob(f"{filename}\\*.[p|j][n|p][g]")
        image_files.sort(key=sort_func1)
        for image in image_files:
            print(image)
            shutil.move(image, f"temp\\{number}.jpg")
            number += 1
        files_temp.pop(0)
        shutil.rmtree(f"{filename}\\")
        times -= 1

        if times == 0:
            sleep(1)
            number -= 1
            to_pack = []
            for i in range(round(number / 2) + 1):
                if 1 + i == number - i:
                    to_pack.append([1 + i])
                else:
                    to_pack.append([1 + i, number - i])
            with contextlib.suppress(IndexError):
                if (
                    to_pack[-1][0] == to_pack[-2][1]
                    and to_pack[-1][1] == to_pack[-2][0]
                ):
                    to_pack.pop(-1)
            os.makedirs("temp_final", exist_ok=True)
            number_temp = 1
            cislo = 0
            for images in to_pack:
                if len(images) == 1:
                    import requests

                    img_data = requests.get(
                        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Black_colour.jpg/1200px-Black_colour.jpg"
                    ).content
                    with open("black.jpg", "wb") as handler:
                        handler.write(img_data)
                    images.append("black")
                    shutil.move("black.jpg", "temp\\black.jpg")

                print(images[0], images[1])
                list_im = [f"temp\\{images[0]}.jpg", f"temp\\{images[1]}.jpg"]
                list_im.reverse()
                if cislo % 2 == 1:
                    imgs = [ImageOps.mirror(Image.open(i)) for i in list_im]
                else:
                    imgs = [Image.open(i) for i in list_im]
                cislo += 1
                min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
                imgs_comb = np.hstack([i.resize(min_shape) for i in imgs])

                imgs_comb = Image.fromarray(imgs_comb)
                imgs_comb.save(f"temp_final\\{number_temp}.jpg")

                number_temp += 1
                if images[1] == "black.jpg":
                    os.remove("black.jpg")
            folder_path = "temp_final"
            cislo = 0
            for filename in os.listdir(folder_path):
                if filename.endswith(".jpg"):
                    img_path = os.path.join(folder_path, filename)
                    img = Image.open(img_path)
                    if cislo % 2 == 1:
                        img = ImageOps.flip(img)
                    cislo += 1
                    pdf_path = os.path.join(folder_path, f"{filename[:-4]}.pdf")
                    print(pdf_path)
                    img.save(pdf_path, "PDF", resolution=100.0)
                    os.remove(img_path)
            pdf_merger = PyPDF2.PdfMerger()
            pdf_files = glob.glob("temp_final\\*.pdf")
            pdf_files.sort(key=sort_func1)
            for filename in pdf_files:
                if filename.endswith(".pdf"):
                    pdf_merger.append(filename)
            pdf_merger.write(f"VOL. {volume}.pdf")
            pdf_merger.close()
            volume += 1
            shutil.rmtree("temp_final")
            shutil.rmtree("temp")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree("temp")
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree("temp_final")
