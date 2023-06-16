import os
import sys
import glob
import argparse
import shutil
from time import sleep
import copy
from math import floor
from PIL import Image, ImageOps
import numpy as np
import PyPDF2
import re


parser = argparse.ArgumentParser()

parser.add_argument("input", help="input folder")
parser.add_argument("-fp", "--file_pattern", help="file pattern same as glob pattern")

args = parser.parse_args()


def sort_func(input_file):
    if args.file_pattern is None:
        input_file = input_file.split("\\")[1].rsplit(".", 1)[0]
        patern = re.compile(
            "^(((V|v)(O|o)(L|l)\.)[0-9]+ (C|c)(H|h).[0-9]+)|((C|c)(H|h).[0-9]+)|((C|c)(H|h)(A|a)(P|p)(T|t)(E|e)(R|r) [0-9]+)$"
        )
        pos = patern.search(input_file)
        input_file = input_file[pos.regs[0][0] : pos.regs[0][1]]
        number = -1
        while True:
            try:
                a = input_file[number : len(input_file)]
                if a[0] == ".":
                    number -= 1
                    continue
                value = float(input_file[number : len(input_file)])
                number -= 1
            except ValueError:
                break
        return value
    else:
        return float(
            input_file.split(args.file_pattern.split("*")[0])[1].split(
                args.file_pattern.split("*")[1]
            )[0]
        )


def sort_func1(input_file):
    input_file = input_file.split("\\")[-1]
    input_file = int(input_file.split(".")[0])
    return input_file


def main():
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
                    print(str(i + 1) + ") " + files_temp[i])
                except IndexError:
                    break
            vstup = input("Select HOW MANY IN A ROW volumes to pack > ")
            if vstup == "*":
                vstup = len(files_temp)
            elif int(vstup) > len(files_temp):
                vstup = len(files_temp)
            else:
                vstup = int(vstup)
            number = 1
            times = vstup
        CbxManager.CbxManager().parse_cbz(file)
        patern = re.compile(
            "^(((V|v)(O|o)(L|l)\.)[0-9]+ (C|c)(H|h).[0-9]+)|((C|c)(H|h).[0-9]+)|((C|c)(H|h)(A|a)(P|p)(T|t)(E|e)(R|r) [0-9]+)$"
        )
        pos = patern.search(file)
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

        to_pack = []
        if times == 0:
            sleep(1)
            number -= 1
            for i in range(round(number / 2) + 1):
                if 1 + i == number - i:
                    to_pack.append([1 + i])
                else:
                    to_pack.append([1 + i, number - i])
            try:
                if (
                    to_pack[-1][0] == to_pack[-2][1]
                    and to_pack[-1][1] == to_pack[-2][0]
                ):
                    to_pack.pop(-1)
            except IndexError:
                pass
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
                    pdf_path = os.path.join(folder_path, filename[:-4] + ".pdf")
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
        try:
            shutil.rmtree("temp")
        except FileNotFoundError:
            pass
        try:
            shutil.rmtree("temp_final")
        except FileNotFoundError:
            pass
