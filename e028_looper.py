#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copy file to destination as they arrive

2024 xaratustrah
"""

import sys, os
import argparse
import datetime
import time
from loguru import logger
import shutil
import toml
import hashlib


def process_loop(from_path, to_path, logfile, sleeptime):
    """
    main copy loop
    """
    for file in os.listdir(from_path):
        fullfilename = os.path.join(from_path, file)
        if not already_copied(fullfilename, logfile):
            logger.info(f"New file arrived: {file}")
            if ready_for_copy(fullfilename, sleeptime):
                logger.success(f"Ready to copy {file}")
                put_into_logfile(fullfilename, logfile)
                c1 = get_checksum(fullfilename)
                logger.info("Checksum of source file: " + c1)
                shutil.copy(fullfilename, to_path)
                c2 = get_checksum(to_path + file)
                logger.info("Checksum of destination file: " + c2)
                if not c1 == c2:
                    logger.error(
                        f"Checksums do not match for {file}! Something is wrong. Aborting..."
                    )
                    exit()
                else:
                    logger.success(f"Checksums match for {file}. Continuing.")


def put_into_logfile(filename, logfile):
    """
    Write into the log file.
    """

    with open(logfile, "a") as f:
        f.write(filename + "\n")


def already_copied(filename, logfile):
    """
    check whether the file is already in the log file
    """

    already_copied = False
    try:
        with open(logfile, "r") as f:
            loglist = f.readlines()

            for line in loglist:
                if filename in line:
                    already_copied = True

    except OSError as e:
        logger.warning("Log file does not exist, creating a new one.")

    return already_copied


def ready_for_copy(filename, sleeptime):
    logger.info("Checking whether file is ready for copy...")
    is_ready = False
    try:
        s1 = os.path.getsize(filename)
        time.sleep(sleeptime)
        s2 = os.path.getsize(filename)
        if s1 == s2:
            is_ready = True
        else:
            is_ready = False
    except OSError:
        is_ready = False
    return is_ready


def get_checksum(filename):
    with open(filename, "rb") as f:
        d = f.read()
        hsh = hashlib.md5(d).hexdigest()

    return hsh


# ----


def main():
    scriptname = "e028_looper"
    __version__ = "v0.0.1"

    default_logfile = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S") + ".txt"

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        nargs=1,
        type=str,
        default=None,
        help="Path and name of the TOML config file.",
    )

    logger.remove(0)
    logger.add(sys.stdout, level="INFO")

    args = parser.parse_args()

    logger.info("{} {}".format(scriptname, __version__))

    # read config file
    config_dic = None
    if args.config:
        logger.info("Configuration file has been provided: " + args.config[0])
        try:
            # Load calibration file
            config_dic = toml.load(args.config[0])
            # check structure of calibration file
            print(config_dic)
            for key in ["from_path", "to_path", "logfile"]:
                assert key in config_dic["paths"].keys()
            for key in ["sleeptime"]:
                assert key in config_dic["settings"].keys()

        except:
            logger.error("Config file does not have required format.")
            exit()

        logger.success("Config file is good.")

        sleeptime = config_dic["settings"]["sleeptime"]
        from_path = config_dic["paths"]["from_path"]
        to_path = config_dic["paths"]["to_path"]
        logfile = config_dic["paths"]["logfile"]

    else:
        logger.error("No Config file provided. Aborting...")
        exit()

    from_path = os.path.join(from_path, "")
    to_path = os.path.join(to_path, "")

    logger.info(f"Copying files from {from_path} to {to_path}")
    logger.info(f"Checking interval {sleeptime} s")
    logger.info("Let us see if there are new files...")
    try:
        while True:
            # Make sure there is a trailing slash at the end of the path

            # start looping process
            process_loop(from_path, to_path, logfile, sleeptime)
            time.sleep(1)
            logger.info("I am waiting for new files...")

    except KeyboardInterrupt:
        logger.success(
            "\nOh no! You don't want me to continue waiting for new files! Aborting as you wish :-("
        )


# ------------------------
if __name__ == "__main__":
    main()
