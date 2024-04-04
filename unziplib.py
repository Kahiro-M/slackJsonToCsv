#!/usr/bin/env python3
# https://gist.github.com/doraTeX/0d79d8ff35710a27bc3e5176cc646b60

import sys
import re
from zipfile import ZipFile
from getpass import getpass

def unzip(argv):

    # if len(sys.argv) == 1:
    if len(argv) == 0:
        # print("Usage: {} ZIP_FILE(S)...".format(sys.argv[0]))
        print("Usage: {} ZIP_FILE(S)...".format(argv[0]))
        exit(0)

    # if len(sys.argv) == 2:
    if len(argv) == 1:
        outdir = 'unzip'

    # if len(sys.argv) == 3:
    if len(argv) == 2:
        # outdir = sys.argv[2]
        outdir = argv[1]

    # for target in sys.argv[1:]:
    for target in argv[0:1]:
        try:
            zip_file = ZipFile(target)
        except Exception as e:
            message = " ".join(filter(lambda x: isinstance(x, str), e.args))
            print("{}: {}".format(message, target))
            exit(1)

        print("Extracting archive: {}".format(target))
        password = None

        for zinfo in zip_file.infolist():
            is_encrypted = zinfo.flag_bits & 0x1
            if is_encrypted and not password:
                password = getpass('Password: ')
                zip_file.setpassword(password.encode('utf-8'))
            if not zinfo.flag_bits & 0x800:
                try:
                    name = zinfo.filename.encode('cp437').decode('utf-8')
                except UnicodeDecodeError:
                    name = zinfo.filename.encode('cp437').decode('cp932')
                zinfo.filename = name

            filename = zinfo.filename

            # Ignore junk files such as .DS_Store or __MACOSX
            components = filename.split("/")
            pattern = r"^(?:\.DS_Store$|__MACOSX$|\._)"
            if {re.match(pattern, c) for c in components} != {None}:
                print("Skipping junk file: {}".format(filename))
                continue

            print("Extracting file: {}".format(filename))
            try:
                zip_file.extract(zinfo,outdir)
            except RuntimeError as e:
                if is_encrypted:
                    print("ERROR: Wrong password")
                else:
                    print("Unknown Error")
                print(e)
                exit(1)
