# Managerie
Configurable rule-based manager for cleaning up the zoo that is your downloads folder.

# Usage
1. Get Managerie.py and Managerie.ini

2. Place anywhere, so long as the ini is in the same folder as the script (maybe in the folder you will be managing?).

3. Configure rules and run!

Multiple instances can be run for different folders, though they need to be kept in their own directories.

# Configuration
## SETTINGS
Debug: (True / False, default True) if debug is enables, a log file will be kept in the working directory
Sort Directory: full path to the folder you want sorted.

## RULES
Files are compared to rules __in the order they are registered.__

Rules can either be set to delete or move a file. The format differs slightly per each:

### delete
```ini
rule_name = del, mode, arguments
```
### move
```ini
rule_name = move, full/path/to/target/folder, mode, arguments
```

For both, mode may be ```list```, ```regex```, ```regex_list```, or ```condition```.

```list``` mode requires that the arguments simply be a list of keywords to match.

```regex``` mode requires exactly one argument which is a python-format regex.

```regex_list``` may be a list of regex, but does not support the use of commas within the expressions themselves.

```condition``` allows an arbitrary logical python statement to be evaluated to make the decision.
Any statement which is in error will be ignored.

## Troubleshooting
If the script crashes before being able to read the config, it'll keep the log file. This generally indicates that the config file has a typo. In fact, most errors are likely due to a typo in the config file, however if nothing can fix it, send me your config file and steps to reproduce the issue.
