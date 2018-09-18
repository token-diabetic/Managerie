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
        # add handling for condition type, need to evaluate string into code


class sorter:

    def __init__(self):
        self.config = configparser.ConfigParser()  # makes config object, when read works like dictionary
        self.debug = False  # saves debug information to log file
        self.sortdir = ""
        self.delrules = []
        self.sortrules = []

        self.numbered_file = re.compile(".* \([0-9]*\)")  # regex for a numbered file (windows duplicate format)
        self.number_splitter = re.compile(" \([0-9]*\)")  # regex that matches number of file for removal

        stderrLogger = logging.StreamHandler()  # creates stream handler that pipes log entries to stdout (console)
        stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))  # sets basic logging format
        logging.getLogger().addHandler(stderrLogger)  # adds handler to logger

        logging.info("Debug Stream Established.")

        try:
            self.get_rules()
        except FileNotFoundError:
            self.unexpected_exit("Please create a config file in script directory according to readme.")

        if self.debug:
            open('managerie_log.txt', 'w').close()  # opens and closes file to make sure it exists
            logging.basicConfig(filename='managerie_log.txt', level=logging.DEBUG)  # sets up log file
            logging.debug("Debug Log File Established.")

        try:
            with os.scandir(self.sortdir) as contents:  # scans given directory and outputs contents
                self.contents = [i for i in contents]  # converts (?) to list format and stores
                for item in self.contents:
                    self.runrules(item, self.contents)
        except FileNotFoundError:
            self.unexpected_exit("Sort directory does not exist")

    def get_rules(self):  # reads file and populates list of rules to follow
        self.config.read("Managerie_old.ini")  # reads file into config object
        self.debug = self.config["SETTINGS"]["Debug"]  # checks if debug is active
        self.sortdir = self.config["SETTINGS"]["Sort Directory"]  # grabs sort directory

        for key, item in enumerate(self.config["DELETE RULES"]):  # loops through part of config
            item = [x.strip() for x in item.split(',')]  # splits comma-separated parts and strips spaces
            name = key
            type = "del"
            matchtype = item[1]
            if matchtype in ("regex", "condition"):
                match = item[2]
            else:
                match = item[2:]
            self.delrules.append(rule(name, type, matchtype, match))  # creates rules

            # config should have deletion rules in the following format:
            # Name = matchtype, match_arg

        for key, item in enumerate(self.config["SORT RULES"]):  # works just about the same as above
            item = [x.strip() for x in item.split(',')]
            name = key
            type = "sort"
            targetfolder = item[0]  # also collects a targetfolder for files matching rule
            matchtype = item[1]
            if matchtype == "regex":
                match = item[2]
            else:
                match = item[2:]
            self.delrules.append(rule(name, type, matchtype, match, targetfolder))

            # config should have sorting rules in the following format:
            # Name = targetfolder, matchtype, match_arg

    def is_duplicate(self, file, target=None):  # checks if file has duplicate in target location, DELETES if true
        if target is not None:  # TODO needs commenting
            with os.scandir(self.sortdir) as contents:
                if re.split(self.number_splitter, file.name)[0] in [os.path.splitext(i.name)[0] for i in contents]:
                    self.delfile(file)
                    return True
        elif self.numbered_file.match(file.name) and (re.split(self.number_splitter, file.name)[0] in [os.path.splitext(i.name)[0] for i in self.contents]):
            self.delfile(file)
            return True
        else:
            return False

    def move(self, file, target):  # moves file to target location, or deletes if duplicate in location
        if not self.is_duplicate(file, target):
            if not os.path.isdir(target):  # checks if path exists
                logging.warning("Target folder does not exist. Creating folder....")
                os.mkdir(target)  # creates path if it does not
            os.rename(file.path, target + file.name)  # attempts to rename file to target path + filename

    def delfile(self, file):  # deletes file or folder
        if file.is_file():
            os.remove(file.path)
        else:
            shutil.rmtree(file.path)

    def runrules(self, file, contents):  # runs a file through all rules to find appropriate action TODO (needs commenting)
        if self.is_duplicate(file):
            logging.debug("File is duplicate in directory. Deleting...")
            self.delfile(file)
            return "Deleted"

        for rule in self.delrules:
            logging.debug("Attempting to match file {} to deletion rule...".format(file.name))
            if rule.matchtype == "regex":
                if re.compile(rule.match).match(file.name):
                    logging.debug("File matches deletion rule {}. Deleting...".format(rule.name))
                    self.delfile(file)
                    return "Deleted"
            elif rule.matchtype == "list":
                if any(True if x in file.name else False for x in rule.match):
                    logging.debug("File matches deletion rule {}. Deleting...".format(rule.name))
                    self.delfile(file)
                    return "Deleted"

        for rule in self.sortrules:
            logging.debug("Attempting to match file {} to sorting rule...".format(file.name))
            if rule.match == "regex":
                if re.compile(rule.match).match(file.name):
                    logging.debug("File matches sorting rule {}. Moving... ".format(rule.name))
                    self.move(file, rule.targetfolder)

        # TODO run through populated rules and apply correct resolution
        # TODO first check dupes, then sort rules, then delete rules
        # TODO implement handling for evaluated rules

    def unexpected_exit(self, msg):  # logs error and exits after waiting long enough for user to read error
        logging.error("ERROR: {}".format(msg))
        time.sleep(5)
        exit()
