"""
Managerie.py / Jackson Callaghan / Jan 2018

Made to automatically sort files from downloads folder to a specified location and subfolders because fuck moodle.
See Readme for instructions.

"""


import os
import configparser
import shutil
import re
import tkinter as tk
from tkinter import messagebox
import time


class Sub:  # makes an easily searchable subfolder and permutations list

    def __init__(self, keyword, permutations, path):

        self.subfolder = keyword
        self.path = path + path + "/" + self.subfolder + '/'
        self.permutations = permutations.split()


class Issue:  # used for setting up list items in the dialog window

    def __init__(self, title, file, resolveaction, dest=None, sort_obj=None):

        self.title = title
        self.file = file  # takes scandir's return rather than path for simplicity & utility
        self.resolveaction = resolveaction  # takes method, either delete or move, to be used as callback
        self.dest = dest
        self.resolved = False  # used to avoid reuse when potentially re-opening dialog for further questioning
        self.sort_obj = sort_obj  # takes instance of sorter for sort method access.
        #  could have just used the sort() method but meh


class CentralKey:  # grabs info from config file and stores for easier access

    def __init__(self):

        self.config = configparser.ConfigParser()  # makes config object and sets up variables
        self.debug = False
        self.deleteManyNumbers = False
        self.askDeleteManyNumbers = False
        self.deleteManyScores = False
        self.askDeleteManyScores = False
        self.deleteUnconfirmedDownloads = False
        self.askDeleteUnconfirmedDownloads = False
        self.deleteOldExes = False
        self.AskdeleteOldExes = False
        self.deleteDuplicates = False
        self.askDeleteDuplicates = False
        self.useGeneralMatches = False
        self.downloads = ""
        self.target = ""
        self.generalPermutations = []
        self.subfolders = []

    def get_info(self):
        try:
            self.config.read("Managerie_old.ini")  # reads file and assigns variables
            self.debug = True if self.config['SETTINGS']["Debug"] == 'True' else False
            self.deleteManyNumbers = True if self.config['SETTINGS'][
                                                 'Delete files with too many numbers'] == 'True' else False
            self.askDeleteManyNumbers = True if self.config['SETTINGS'][
                                                    'Ask to delete many numbers'] == 'True' else False
            self.deleteManyScores = True if self.config['SETTINGS'][
                                                'Delete files with too many underscores/dashes'] == 'True' else False
            self.askDeleteManyScores = True if self.config['SETTINGS'][
                                                   'Ask to delete many underscores'] == 'True' else False
            self.deleteUnconfirmedDownloads = True if self.config['SETTINGS'][
                                                          'Delete old unfinished downloads'] == 'True' else False
            self.askDeleteUnconfirmedDownloads = True if self.config['SETTINGS'][
                                                             'Ask to delete unfinished'] == 'True' else False
            self.deleteOldExes = True if self.config['SETTINGS']['Delete old installers'] == 'True' else False
            self.AskdeleteOldExes = True if self.config['SETTINGS']['Ask to delete old installers'] == 'True' else False
            self.deleteDuplicates = True if self.config['SETTINGS'][
                                                'Delete numbered duplicate files'] == 'True' else False
            self.askDeleteDuplicates = True if self.config['SETTINGS']['Ask to delete duplicates'] == 'True' else False
            self.useGeneralMatches = True if self.config['SETTINGS']['Use General Matches'] == 'True' else False
            self.downloads = self.config['LOCATIONS']['DownloadsFolder'].replace("\\", "/")
            self.target = self.config['LOCATIONS']['TargetFolder'].replace("\\", "/")
            self.generalPermutations = self.config['GENERAL KEYWORDS']['keywords'].split()
            self.subfolders = [Sub(key, data, self.target) for key, data in self.config.items('KEYWORDS')]

        except FileNotFoundError:  # opens message box to relay info then shuts down program before any sorting occurs
            err = messagebox.showerror("File Import", message="ERROR: File not found. \n "
                                       "Please ensure Managerie_old.ini exists and is formatted properly")
            if err:
                exit()


class ScrollFrame(tk.Frame):  # scrollable frame, credit to Bryan Oakley because I couldn't figure this shit out
    def __init__(self, root):

        tk.Frame.__init__(self, root)
        self.canvas = tk.Canvas(root, borderwidth=0)
        self.frame = tk.Frame(self.canvas)
        self.scrollbar = tk.Scrollbar(root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4, 4), window=self.frame, anchor=tk.NW, tags="self.frame")

        self.frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        self.optselect = []
        self.options = {}  # holds option selections for general matches
        self.checked = {}  # holds checkbuttons for deletion confirmations
        self.labels = {}  # holds all the checkbutton/optionmenu objects for ease of access

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(round(-1*event.delta/120, 0)), "units")

    def populate(self, issues, folders):  # creates the shoddy list of problems with action items
        self.optselect = [s.subfolder for s in folders]
        self.optselect.append("KEEP")
        self.optselect.append("DELETE")
        for row, issue in enumerate(issues):
            if not issue.resolved:
                tk.Label(self.frame, text=issue.title.split(":")[0], borderwidth="1", relief="solid")\
                    .grid(row=row, column=0, sticky=tk.EW)
                tk.Label(self.frame, text=issue.title.split(":")[1], borderwidth="1", relief="solid")\
                    .grid(row=row, column=1, sticky=tk.EW)
                if issue.dest is not None:
                    self.options[issue.title] = tk.StringVar()
                    self.options[issue.title].set("KEEP")
                    self.labels[issue.title] = tk.OptionMenu(self.frame, self.options.get(issue.title),
                                                             *tuple(self.optselect))
                    self.labels[issue.title].grid(row=row, column=2, sticky=tk.EW)
                else:
                    self.checked[issue.title] = tk.IntVar()
                    self.labels[issue.title] = tk.Checkbutton(self.frame, variable=self.checked[issue.title])
                    self.labels[issue.title].grid(row=row, column=2, sticky=tk.EW)

    def on_frame_configure(self, event):  # ensures the scrolling area fits the canvas or something
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class Dialog:  # defines dialog window with list of issues raised and checkbuttons/option menus to control files

    def __init__(self, master, issues, subfolders):

        self.master = master
        self.scrollframe = ScrollFrame(master)  # holds most of the window
        self.buttonframe = tk.Frame(master)  # holds the buttons
        self.issues = issues
        self.resolved = 0
        self.subfolders = subfolders

        self.scrollframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.buttonframe.pack(side=tk.BOTTOM, fill=tk.X)

        self.checkall = tk.Button(self.buttonframe, text="Check all", command=self.check_all)
        self.uncheckall = tk.Button(self.buttonframe, text="Uncheck all", command=self.uncheck_all)
        self.button1 = tk.Button(self.buttonframe, text="Confirm", command=self.cleanup)

        self.checkall.pack(side=tk.LEFT)
        self.uncheckall.pack(side=tk.LEFT)
        self.button1.pack(side=tk.LEFT)
        self.button2 = tk.Button(self.buttonframe, text="Cancel", command=exit)
        self.button2.pack(side=tk.LEFT)

        ScrollFrame.populate(self.scrollframe, self.issues, self.subfolders)

    def check_all(self):
        for i in [self.scrollframe.labels[i] for i in [x.title for x in self.issues] if i in [y for y in self.scrollframe.checked.keys()]]:
            i.select()

    def uncheck_all(self):
        for i in [self.scrollframe.labels[i] for i in [x.title for x in self.issues] if i in [y for y in self.scrollframe.checked.keys()]]:
            i.deselect()

    def cleanup(self):  # deals with resolutions of each issue and then closes window
        for title, value in self.scrollframe.checked.items():

            issue = [i for i in self.issues if i.title == title][0]  # finds title matching issue for methods etc
            if value.get() == 1:  # checks if checkbutton is checked
                issue.resolveaction(issue.file)  # calls back to the resolveaction (in this case delete)
                issue.resolved = True

            else:
                issue.sort_obj.sort(issue.file, None, skip=True)
                issue.resolved = True

        for title, value in self.scrollframe.options.items():
            issue = [i for i in self.issues if i.title == title][0]
            selection = value.get()
            if selection == "KEEP":
                issue.resolved = True
                pass
            elif selection == "DELETE":
                if issue.file.is_file():
                    os.remove(issue.file.path)
                    issue.resolved = True
                else:
                    shutil.rmtree(issue.file.path)
                    issue.resolved = True
            else:
                print(issue.dest)
                print(selection)
                destfolder = issue.dest + selection + "/" + issue.file.name
                print(destfolder)
                issue.resolveaction(issue.file, False, destfolder)  # calls back to resolveaction with selected dest
                issue.resolved = True

        self.master.destroy()


class Sorter:  # center of the program, contains all important methods and runs sorting.

    def __init__(self):

        self.key = CentralKey()
        self.issues = []

    def makewindow(self):  # reusable way to make a dialog window
        root = tk.Tk()
        GUI = Dialog(root, self.issues, self.key.subfolders)
        root.mainloop()

    def delete_file(self, item, confirm=False, reason=None):
        # deletes file or raises issue if confirmation is required

        if confirm:
            self.issues.append(Issue("{}: {}".format(item.name, reason), item, self.delete_file, None, self))
        else:
            if item.is_file():
                os.remove(item.path)
            else:
                shutil.rmtree(item.path)

    def move_file(self, item, confirm, dest=None, reason=None):
        # moves file or raises issue if confirmation is required
        if confirm:
            self.issues.append(Issue("{}: {}".format(item.name, reason), item, self.move_file, dest, self))
        else:
            os.rename(item.path, dest)

    def checksubs(self):  # checks if defined subfolders exist and creates them if not

        for s in self.key.subfolders:
            expected_path = self.key.target + "/" + s.subfolder + "/"
            if not os.path.isdir(expected_path):
                print("DEBUG: path {0} does not exist. Creating...".format(expected_path)) if self.key.debug else None
                os.mkdir(expected_path)
                print("DEBUG: Creation successful.") if self.key.debug else None

    def check_file_old(self, file):  # compares file creation time to current time to determine age
        current_time = time.time()
        creation_time = file.stat().st_mtime

        if (current_time - 3600) > creation_time:  # returns true if older than 1 hour
            return True
        else:
            return False

    def sort(self, item, contents, skip=False):
        # sorts individual files, separated so unresolved issues can be re-sorted (figure out how that works)

        numDupRe = re.compile(".* \([0-9]*\)")  # sets up regex to match numbered duplicates
        splitter = re.compile(" \([0-9]*\)")  # similar regex for cutting off just the original filename
        num_matcher = re.compile("[0-9]")

        if not skip:
            # checks if item should skip delete checks, assuming user didn't delete file for one reason,
            # they probably don't want to delete it for another
            # these also come before in order to avoid possible problems with files with too many numbers
            # happening to have a class number, etc
            file_old = self.check_file_old(item)

            if item.name in ("Managerie_old.pyw", "Managerie_old.ini"):
                return

            if ((item.name.lower().endswith('.exe') or item.name.lower().endswith('.msi')) and file_old) and self.key.deleteOldExes:
                self.delete_file(item, self.key.AskdeleteOldExes, "old installer")
                return

            elif (item.name.lower().endswith('.crdownload') and file_old)\
                    and self.key.deleteUnconfirmedDownloads:
                self.delete_file(item, self.key.askDeleteUnconfirmedDownloads, "old unconfirmed download")
                return

            elif (numDupRe.match(os.path.splitext(item.name)[0]) and
                  (re.split(splitter, item.name)[0] in [os.path.splitext(i.name)[0] for i in contents])) and self.key.deleteDuplicates:
                self.delete_file(item, self.key.askDeleteDuplicates, "duplicate")
                return

            elif (len([i for i in item.name if num_matcher.match(i)]) >= 10) and self.key.deleteManyNumbers:
                self.delete_file(item, self.key.askDeleteManyNumbers, "too many numbers")
                return

        for p in self.key.subfolders:  # checks for specific matches
            if any([True if i in item.name.lower() else False for i in p.permutations]):
                print("DEBUG: Found match. Moving...") if self.key.debug else None
                self.move_file(item, False, self.key.target + "/" + p.subfolder + "/" + item.name)
                return

        if self.key.useGeneralMatches:  # checks for general matches
            for p in self.key.generalPermutations:
                if p in item.name.lower():
                    self.move_file(item, True, self.key.target + "/", "general match")

    def sort_now(self):  # runs initial sorting operation

        self.checksubs()
        print("DEBUG: Scanning download contents...") if self.key.debug else None
        with os.scandir(self.key.downloads) as contents:
            cont = [i for i in contents]
            for item in cont:
                self.sort(item, cont)

        while len([i for i in self.issues if not i.resolved]) > 0:  # runs until all issues have been resolved
            self.makewindow()  # starts dialog window


if __name__ == "__main__":

    sorter = Sorter()
    sorter.key.get_info()
    sorter.sort_now()
