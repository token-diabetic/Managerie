"""
Managerie.py | Jackson Callaghan | Sep 2018

Managerie 2.0 - sorts through files according to basic rules, and does not prompt user for permission to delete or move
files. See readme for information.
"""

import os
import configparser
import shutil
import re
import time
import logging

class rule:

    def __init__(self, name, type, matchtype, match, targetfolder=None):
        self.name = name
        self.type = type
        self.matchtype = matchtype
        self.match = match
        self.targetfolder = targetfolder

    def prep_regex(self):
        if self.matchtype == "regex":
            temp = self.match
            self.match = re.compile(temp)

    def checkmatch(self, file):
        o = 0
        # check if file matches rule, add handling for checking whether matching with regex or list


class sorter:

    def __init__(self):
        self.config = configparser.ConfigParser()  # makes config object
        self.debug = False  # saves debug information to log file
        self.sortdir = ""
        self.delrules = []
        self.sortrules = []

        stderrLogger = logging.StreamHandler()
        stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        logging.getLogger().addHandler(stderrLogger)

        logging.info("Debug Stream Established.")

        try:
            self.get_rules()
        except FileNotFoundError:
            logging.error("ERROR: Config file not found. "
                          "Please create a config file in script directory according to readme.")
            time.sleep(5)
            exit()

        if self.debug:
            open('managerie_log.txt', 'w').close()
            logging.basicConfig(filename='managerie_log.txt', level=logging.DEBUG)

    def get_rules(self):  # reads file and populates list of rules to follow
        self.config.read("Managerie_old.ini")  # reads file into config object
        self.debug = self.config["SETTINGS"]["Debug"]  # checks if debug is active
        self.sortdir = self.config["SETTINGS"]["Sort Directory"]  # grabs sort directory

        for key, item in enumerate(self.config["DELETE RULES"]):
            item = [x.strip() for x in item.split(',')]
            name = key
            type = "del"
            matchtype = item[1]
            if matchtype == "regex":
                match = item[2]
            else:
                match = item[2:]
            self.delrules.append(rule(name, type, matchtype, match))

        for key, item in enumerate(self.config["SORT RULES"]):
            item = [x.strip() for x in item.split(',')]
            name = key
            type = "sort"
            targetfolder = item[0]
            matchtype = item[1]
            if matchtype == "regex":
                match = item[2]
            else:
                match = item[2:]
            self.delrules.append(rule(name, type, matchtype, match, targetfolder))




    def is_duplicate(self, file, target):
        o = 0
        # check if file is duplicate of any file in given location or of given file
        # this means you have to check if target is file or location

    def move(self, file, target):
        o = 0
        # move given file to target location
        # check if file is duplicate of file in sort location and delete if so

    def delfile(self, file):
        o = 0
        # delete given file

    def runrules(self):
        o = 0
        # run through populated rules and apply correct resolution
        # first check dupes, then sort rules, then delete rules