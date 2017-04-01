from sys import argv, exit
import os
import hashlib
from shutil import copyfile
import json
from time import sleep

def sha256checksum(file):
    with open(file, 'rb') as f:
        m = hashlib.sha256()
        while True:
            data = f.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


def id_file(file):
    if sha256checksum(file) not in known_files:
        with open(file, "rb") as bf:
            head = [next(bf) for x in range(1)]
        if "PNG" in str(head):
            copyfile(file, output_dir + "/images/" + file.split("/")[-1] + ".png")
        elif "GIF" in str(head):
            copyfile(file, output_dir + "/images/" + file.split("/")[-1] + ".gif")
        elif "webmB" in str(head):
            copyfile(file, output_dir + "/videos/" + file.split("/")[-1] + ".webMB")
        elif "mp4" in str(head):
            copyfile(file, output_dir + "/videos/" + file.split("/")[-1] + ".mp4")
        elif "JFIF" in str(head) or "\\xff\\xd8\\xff\\xfe\\" in str(head)[:20]:
            copyfile(file, output_dir + "/images/" + file.split("/")[-1] + ".jpeg")
        elif "\\x1f\\x8b\\x08\\" in str(head)[:20]:
            copyfile(file, output_dir + "/compressed/" + file.split("/")[-1] + ".gzip")
        else:
            print(file, "not identified, unknown header")
            copyfile(file, output_dir + "/unknown/" + file.split("/")[-1])


def id_json(data):
    if "username" in data:
        print("Userdata found")
        copyfile(working_dir + "/" + file, output_dir + "/data/userinfo.json")
    if "author" in data[0]:
        print("Found chat history of", len(data), "entries")
        copyfile(working_dir + "/" + file, output_dir + "/data/chat_history/" + file + ".json")
    if "type" in data[0] and "user" in data[0]:
        print("Found the friends list")
        copyfile(working_dir + "/" + file, output_dir + "/data/friendlist.json")

    sleep(2)

if len(argv) < 2:
    exit("ERROR: Incorrect usage, use " + argv[0] + " -h to check the help file")

if "-h" in argv:
    print("Usage discrecorder.py -i [input folder] [OPTIONS] ...")
    print("\nOptions\t\t\t Meaning")
    print("-i\t\t\t Input folder. Point this to the root folder of the file system to inspect")
    print("\t\t\t This is generally the mount location of the retrieved image")
    print("-o\t\t\t Output folder. All info and retrieved data will be placed here")
    print("-h\t\t\t Show this output")
    exit()

if "-i" not in argv:
    exit("ERROR: -i is not optional! use discrecorder.py -h for help")

path_flag = False
for x in range(1,len(argv)):
    if path_flag:
        path_flag = False
        continue
    if argv[x] == "-i":
        if os.path.exists(argv[x+1]):
            target_dir = argv[x+1]
            path_flag = True
            continue
        else:
            exit("Path not found: " + argv[x+1])
    elif argv[x] == "-o":
        if os.path.exists(argv[x+1]):
            output_dir = argv[x+1] + "/discrecorder_extract/"
            path_flag = True
            continue
        else:
            exit("Path not found: " + argv[x+1])
    else:
        exit("Unknown argument, use -h for help")


#target_dir = "/mnt/"
#output_dir = "/sne/home/fmijnen/discord_extract_windows/"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    os.makedirs(output_dir + "/images/")
    os.makedirs(output_dir + "/videos/")
    os.makedirs(output_dir + "/compressed/")
    os.makedirs(output_dir + "/data/")
    os.makedirs(output_dir + "/data/chat_history")
    os.makedirs(output_dir + "/data/sqlite_db")
    os.makedirs(output_dir + "/unknown/")
    os.makedirs(output_dir + "/attachments/")
else:
    print("Output dir already exists, are you sure you want to continue? Press Enter")
    input()

root_dir = os.listdir(target_dir)

known_files = []
with open("known_files.txt", "r") as f:
    for line in f:
        known_files.append(line[:-1])

if "etc" in root_dir and "proc" in root_dir and "dev" in root_dir:
    print("Linux detected")
    print("Looking for discord data")
    discord_path = ""
    for root, dirs, files in os.walk(target_dir):
        for subdir in dirs:
            if subdir == "discord":
                discord_dir = os.listdir(os.path.join(root, subdir))
                if "Cookies" in discord_dir and "GPUCache" in discord_dir and "Local Storage" in discord_dir and "modules.log" in discord_dir:
                    discord_path = os.path.join(root, subdir)
                    break
        if discord_path:
            break

    print("Discord data found. Starting data extraction.")

    cache_dir = os.listdir(discord_path + "/Cache/")
    for file in cache_dir:
        id_file(discord_path + "/Cache/" + file)

    # Grab SQLite DBs
    copyfile(discord_path + "Cookies", output_dir + "data/sqlite_db/Cookies.sqlite3")
    copyfile(discord_path + "Local\ Storage/https_discordapp.com_0.localstorage", output_dir + "data/sqlite_db/https_discordapp.com_0.localstorage.sqlite3")

    print("Done looking through cache. Running binwalk on all unknown data files...")
    os.system("binwalk -e " + output_dir + '/unknown/*' + ' -C' + output_dir + '/unknown -q')
    print("Done binwalking, now looking for interesting data")
    for root, dirs, files in os.walk(output_dir + '/unknown/'):
        for subdir in dirs:
            working_dir = output_dir + '/unknown/' + subdir
            for file in subdir_content:
                subdir_content = os.listdir(working_dir)
                with open(working_dir + "/" + file) as data_file:
                    try:
                        data = json.load(data_file)

                        print(file, "Is a JSON file")
                        print("Identifying JSON file from known discord files...")
                        id_json(data)


                    except:
                        continue

elif "Windows" in root_dir and "Program Files" in root_dir:
    print("Windows detected")
    print("Looking for discord data")
    discord_local_path = ""
    discord_roaming_path = ""
    for root, dirs, files in os.walk(target_dir):
        for subdir in dirs:
            if subdir == "discord" or subdir=="Discord":
                discord_dir = os.listdir(os.path.join(root, subdir))
                if "Cookies" in discord_dir and "Cache" in discord_dir and "Local Storage" in discord_dir and "modules.log" in discord_dir:
                    discord_roaming_path = os.path.join(root, subdir)
                elif "packages" in discord_dir and "app.ico" in discord_dir:
                    discord_local_path = os.path.join(root, subdir)

        if discord_local_path and discord_roaming_path:
            break

    print("Discord data found. Starting data extraction.")

    cache_dir = os.listdir(discord_roaming_path + "/Cache/")
    for file in cache_dir:
        id_file(discord_roaming_path + "/Cache/" + file)

    # Grab SQLITE DB's
    copyfile(discord_roaming_path + "/Cookies", output_dir + "data/sqlite_db/Cookies.sqlite3")
    copyfile(discord_roaming_path + '/Local Storage/https_discordapp.com_0.localstorage', output_dir + "data/sqlite_db/https_discordapp.com_0.localstorage.sqlite3")

    print("Done looking through cache. Running binwalk on all unknown data files...")
    os.system("binwalk -e " + output_dir + '/unknown/*' + ' -C' + output_dir + '/unknown -q')
    print("Done binwalking, now looking for interesting data")

    for root, dirs, files in os.walk(output_dir + '/unknown/'):
        for subdir in dirs:
            working_dir = output_dir + '/unknown/' + subdir
            subdir_content = os.listdir(working_dir)
            for file in subdir_content:
                with open(working_dir + "/" + file) as data_file:

                    try:
                        data = json.load(data_file)

                        print(file, "Is a JSON file, Identifying from known discord files...")
                        id_json(data)
                    except (json.decoder.JSONDecodeError, UnicodeDecodeError, KeyError):
                        # Ignore json errors
                        continue

else:
    exit("Could not identify OS")

os.system("python parse.py " + output_dir)