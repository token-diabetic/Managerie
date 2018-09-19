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

    def __str__(self):
        return "{}: {}, {}, {}, {}".format(self.name, self.type, self.matchtype, self.match, self.targetfolder)

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
        self.config = configparser.ConfigParser()  # makes config object, when read works like list
        self.debug = False  # saves debug information to log file
        self.sortdir = ""
        self.rules = []
        self.contents = None

        self.numbered_file = re.compile(".*\([0-9]*\)")  # regex for a numbered file (windows duplicate format)
        self.number_splitter = re.compile("\([0-9]*\)")  # regex that matches number of file for removal

        open('managerie_log.txt', 'w').close()  # opens and closes file to make sure it exists
        logging.basicConfig(filename='managerie_log.txt', level=logging.DEBUG)  # sets up log file
        logging.debug("Debug Log File Established.")
        stderrLogger = logging.StreamHandler()  # creates stream handler that pipes log entries to stdout (console)
        stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))  # sets basic logging format
        logging.getLogger().addHandler(stderrLogger)  # adds handler to logger

        logging.info("Debug Stream Established.")

        try:
            self.get_rules()
        except (FileNotFoundError, KeyError):
            self.unexpected_exit("Please create a config file in script directory according to readme.")

        logging.debug("Got rules:")
        for x in self.rules:
            logging.debug(x)

    def sort(self):
        logging.debug("Attempting to scan directory {}".format(self.sortdir))
        try:
            with os.scandir(self.sortdir) as contents:  # scans given directory and outputs contents
                self.contents = [i for i in contents]  # converts (?) to list format and stores
                for item in self.contents:
                    self.runrules(item, self.contents)
                    logging.debug("")
        except FileNotFoundError:
            self.unexpected_exit("Sort directory does not exist")
        logging.debug("Sort Complete!")

    def get_rules(self):  # reads file and populates list of rules to follow
        self.config.read("Managerie.ini")  # reads file into config object
        self.debug = self.config["SETTINGS"]["Debug"]  # checks if debug is active
        self.sortdir = self.config["SETTINGS"]["Sort Directory"]  # grabs sort directory

        for key, item in enumerate(self.config["RULES"]):  # loops through rule part of config
                rule_parse = [x.strip() for x in self.config["RULES"][item].split(',')]  # splits comma-separated parts and strips spaces
                logging.debug("Grabbed Rule {}:{}".format(item, rule_parse))
                name = item
                type = rule_parse[0]
                targetfolder = None if type != "move" else rule_parse[1]
                matchtype = rule_parse[1 if type != "move" else 2]
                if matchtype in ("regex", "condition"):
                    match = "".join(rule_parse[2 if type != "move" else 3:])
                else:
                    match = rule_parse[2 if type != "move" else 3:]
                self.rules.append(rule(name, type, matchtype, match, targetfolder))  # creates rules

                # config should have deletion rules in the following format:
                # Name = matchtype, match_arg

            # config should have sorting rules in the following format:
            # Name = targetfolder, matchtype, match_arg

    def is_duplicate(self, file, target=None):  # checks if file has duplicate in target location, DELETES if true
        logging.debug("Checking if file {} is duplicate...".format(file.name))
        if target is not None:  # checks if there's a target location to check
            with os.scandir(self.sortdir) as contents:  # opens target location and scans files into list of file objects
                if re.split(self.number_splitter, file.name)[0] in [os.path.splitext(i.name)[0] for i in contents]:
                    self.delfile(file)
                    return True
        elif self.numbered_file.match(file.name):  # checks if file is a numbered file
            if re.split(self.number_splitter, file.name)[0] in [os.path.splitext(i.name)[0] for i in self.contents]:
                self.delfile(file)
                return True
        else:
            return False

    def move(self, file, target):  # moves file to target location, or deletes if duplicate in location
        if not self.is_duplicate(file, target):
            if not os.path.isdir(target):  # checks if path exists
                logging.warning("Target folder does not exist. Creating folder....")
                os.mkdir(target)  # creates path if it does not
            os.rename(file.path, target + '/' + file.name)  # attempts to rename file to target path + filename

    def delfile(self, file):  # deletes file or folder
        if file.is_file():
            os.remove(file.path)
        else:
            shutil.rmtree(file.path)

    def resolve(self, file, rule):  # decides whether to move or delete file based on rule
        if rule.type == "del":
            logging.debug("File {} matches deletion rule {}. Deleting...".format(file.name, rule.name))
            self.delfile(file)
            return "deleted"
        elif rule.type == "move":
            logging.debug("File {} matches sorting rule {}. Moving...".format(file.name, rule.name))
            self.move(file, rule.targetfolder)
            return "moved"

    def runrules(self, file, contents):  # runs a file through all rules to find appropriate action
        if file.name in ("Managerie.ini", "Managerie.py"):
            logging.debug("File is Managerie-critical file. Skipping...")
            return "Ignored"
        if file.name == "managerie_log.txt":
            logging.debug("File is managerie log. {}...".format("Deleting" if not self.debug else "Skipping"))
            if self.debug:
                return "Ignored"
            else:
                self.delfile(file)

        if self.is_duplicate(file):  # checks if file is duplicate
            logging.debug("File is duplicate in directory. Deleting...")
            return "Deleted"

        logging.debug("Attempting to match file {} to rule...".format(file.name))
        for rule in self.rules:  # checks if file matches sorting rule
            if rule.matchtype == "regex":
                if re.compile(rule.match).match(file.name):  # checks against given regex
                    return self.resolve(file, rule)
            elif rule.matchtype == "list":
                if any(True if x.lower() in file.name.lower() else False for x in rule.match):  # checks if file has any keywords in it
                    return self.resolve(file, rule)
            elif rule.matchtype == "condition":
                try:
                    if eval(rule.match):  # evaluates code given by config for checking arbitrary conditions
                        return self.resolve(file, rule)
                except:
                    logging.debug("Conditional code failed. Skipping...")
                    continue
            elif rule.matchtype == "regex_list":
                if any(True if re.compile(x).match(file.name) else False for x in rule.match):
                    return self.resolve(file, rule)

    def unexpected_exit(self, msg):  # logs error and exits after waiting long enough for user to read error
        logging.error(msg)
        time.sleep(5)
        exit()


mysorter = sorter()
mysorter.sort()
