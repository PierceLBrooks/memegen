
# Author: Pierce Brooks

import io
import os
import sys
import yaml
import base64
import zipfile
from PIL import Image, ImageDraw, ImageFont, ImageSequence

archive = None

def load(script):
    global archive
    path = os.path.join(os.getcwd(), script+".zip")
    if (os.path.exists(path)):
        descriptor = open(path, "rb")
        data = descriptor.read()
        descriptor.close()
        archive = base64.b64encode(data).decode()
    else:
        path = os.path.join(os.getcwd(), "templates")
        if (os.path.exists(path)):
            content = io.BytesIO()
            with zipfile.ZipFile(content, "a", zipfile.ZIP_DEFLATED, False) as zf:
                for root, folders, files in os.walk(path):
                    for name in files:
                        name = os.path.join(root, name)
                        descriptor = open(name, "rb")
                        data = descriptor.read()
                        descriptor.read()
                        zf.writestr(str("templates/"+os.path.relpath(name, path)).replace("\\", "/"), io.BytesIO(data).getvalue())
            archive = base64.b64encode(content.getvalue()).decode()
            path = os.path.join(os.getcwd(), script+".zip")
            descriptor = open(path, "wb")
            descriptor.write(base64.b64decode(archive))
            descriptor.close()
    return archive

def run(script, target, font, labels):
    global archive
    if (archive == None):
        if (load(os.path.basename(script)) == None):
            return 0
    data = base64.b64decode(archive)
    data = io.BytesIO(data)
    zf = zipfile.ZipFile(data)
    files = {}
    prefix = "templates/"
    for info in zf.filelist:
        key = info.filename
        if (len(key) == 0):
            continue
        if not (key.startswith(prefix)):
            continue
        key = key[len(prefix):]
        #print(str(info))
        files[key] = info
    extensions = {}
    templates = {}
    images = {}
    for key in files:
        if (key[(len(key)-1):] == "/"):
            continue
        if not (("/" in key) or ("." in key)):
            continue
        prefix = key[:key.index("/")]
        if not (prefix in images):
            images[prefix] = []
        if (key.endswith(".yml")):
            data = zf.read(files[key])
            data = data.decode()
            data = yaml.load(data, yaml.Loader)
            templates[prefix] = data
        else:
            extension = key[(key.rindex(".")+1):]
            if not (extension in extensions):
                extensions[extension] = 0
            extensions[extension] += 1
            images[prefix].append(key)
    print(str(extensions))
    if not (target in templates):
        return -1
    template = templates[target]
    print(str(template))
    if (labels == None):
        if ("example" in template):
            labels = template["example"]
    if (labels == None):
        return -2
    if not ("text" in template):
        return -3
    lines = template["text"]
    if (len(lines) < len(labels)):
        return -4
    image = None
    for i in range(len(images[target])):
        if (images[target][i][(len(target)+1):].startswith("default")):
            image = images[target][i]
            break
    if (image == None):
        return -5
    if not (os.path.exists(font)):
        return -6
    if not (font.endswith(".ttf")):
        return -7
    extension = image[(image.rindex(".")+1):].lower()
    frames = []
    image = zf.read(files[image])
    image = io.BytesIO(image)
    image = Image.open(image)
    width = float(image.size[0])
    height = float(image.size[1])
    if (extension == "gif"):
        for frame in ImageSequence.Iterator(image):
            frame = frame.copy().convert("RGBA")
            frames.append(frame)
    else:
        frames.append(image.convert("RGBA"))
    font = ImageFont.truetype(font, 20)
    for frame in frames:
        draw = ImageDraw.Draw(frame)
        for i in range(len(labels)):
            label = labels[i]
            line = lines[i]
            position = []
            alignment = ""
            if ("align" in line):
                alignment += line["align"]
            else:
                alignment += "center"
            if ("anchor_x" in line):
                position.append(int(float(line["anchor_x"])*width))
            if ("anchor_y" in line):
                position.append(int(float(line["anchor_y"])*height))
            while (len(position) < 2):
                position.append(0)
            draw.text(tuple(position), label, font=font, align=alignment)
    if (len(frames) > 1):
        frames[0].save(script+"."+extension, save_all=True, append_images=frames[1:], duration=int(len(frames)*6), loop=0, format=extension.upper())
    else:
        frames[0].save(script+"."+extension, format=extension.upper())
    return 1

def launch(arguments):
    if (len(arguments) < 3):
        return False
    script = arguments[0]
    target = arguments[1]
    font = arguments[2]
    labels = None
    if (len(arguments) > 3):
        labels = arguments[3:]
    result = run(script, target, font, labels)
    print(str(result))
    if not (result > 0):
        return True
    return False

if (__name__ == "__main__"):
    print(str(launch(sys.argv)))

sys.exit()

