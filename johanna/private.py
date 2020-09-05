#!/usr/bin/env python
# coding: utf-8

"""
let's see whether we get the internals hidden away from the johanna module interface.

Created: 29.08.20
"""

import os
import sys
from pathlib import Path
import configparser
import logging
from logging.handlers import RotatingFileHandler
from time import perf_counter, process_time, sleep
import tracemalloc
import sqlite3
from typing import Union
import json
from collections import defaultdict

import requests
from docopt import docopt, DocoptExit, DocoptLanguageError


_DOTFOLDER: Path = None
_INIFILE: Path = None
_CONFIG: configparser.ConfigParser = None
_DBFOLDER: Path = None
_DBNAME: str = None
_DBPATH: Path = None

def _initialize(dotfolder: Path = None, dbname: str = None):
    global _DOTFOLDER, _INIFILE, _CONFIG, _DBFOLDER, _DBNAME, _DBPATH

    # ensure dotfolder
    if not dotfolder:
        if "JOHANNA" in os.environ:
            dotfolder = Path(os.environ["JOHANNA"])
        else:  # Fallback
            dotfolder = Path(os.environ["HOME"]) / ".johanna"
    if not dotfolder.exists():
        dotfolder.mkdir()
    _DOTFOLDER = dotfolder
    # Application will not have to care about filename
    _INIFILE = dotfolder / "johanna.ini"

    # get as most messages in log as possible
    # TODO make logging configurable via .ini
    _init_logging(collective=True, console=True, process=True)

    # create init-file in dotfolder
    _CONFIG = configparser.ConfigParser()
    if _INIFILE.exists():
        logging.info(f"Configuration file: {_INIFILE} OK")
    else:
        logging.info(f"Configuration file: {_INIFILE} will be created")
        _INIFILE.touch()
    _CONFIG.read(_INIFILE)

    # create database folder.
    # You can
    #   1. create another
    #   2. move DB files to there and
    #   3. adapt [databases]folder
    # at any point in time (between scheduled runs) if you like.
    #
    if not _CONFIG.has_section("databases"):
        _CONFIG.add_section("databases")
    if "folder" in _CONFIG["databases"]:
        _DBFOLDER = Path(_CONFIG["databases"]["folder"])
    else:
        logging.info(f"Defaulting database folder to {_DOTFOLDER}")
        _DBFOLDER = _DOTFOLDER
        _CONFIG["databases"]["folder"] = str(_DOTFOLDER)
        with open(_INIFILE, "w") as fp:
            _CONFIG.write(fp)
    logging.info(f"Databases go to {_DBFOLDER}")
    if _DBFOLDER.exists():
        logging.info("Using existing folder")
    else:
        logging.info(f"Creating {_DBFOLDER}...")
        _DBFOLDER.mkdir()

    # database will be implicitely created by apply_schema called from application
    _DBNAME = dbname if dbname else "johanna.sqlite"
    _DBPATH = _DBFOLDER / _DBNAME

    logging.info("Johanna at your service.")


def get(section, key, default=None):
    if not _CONFIG:
        raise RuntimeError("johanna.get() before initialization")
    if section in _CONFIG:
        if key in _CONFIG[section]:
            return _CONFIG[section][key]
    return default


# set the following to true if mail should get an "[FAILURE] - " prefix
ERROR = False

_LOGGING_FMT = "%(asctime)s [%(levelname)s] %(message)s"

# simple container for singleton data
# cf. https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
_ROTATING_FILE_PATH = None
_ROTATING_FILE_HANDLER = None
_STDOUT_HANDLER = None
_FILE_PATH = None
_FILE_HANDLER = None


def _init_logging(collective: bool = False, console: bool = False, process: bool = False) -> None:
    """
    Logs shall be initialized as one of the first steps in bootstrapping.
    While all options default to False, at least one must be true. If none is supplied,
    console log will be enabled.

    :param collective: write to a set of rotating logfiles in ~/.luechenbresse
    :param console: write to console (stdout)
    :param process: write to a logfile unique to this process
    :return: nothing. However, a first log message is emitted.
    """
    # TODO run this on import?
    # DONE on/off for log handlers via parameter to support e.g. notebooks that do not do runwise logging

    global _ROTATING_FILE_PATH, _ROTATING_FILE_HANDLER, _STDOUT_HANDLER, _FILE_PATH, _FILE_HANDLER

    # avoid blunt abuse
    if _ROTATING_FILE_PATH or _STDOUT_HANDLER or _FILE_HANDLER:
        return

    # we need some device at least
    if not collective and not process:
        console = True

    handlers = []
    remark = []

    if collective:
        # default.log with 10 rotating segments of 100k each -> 1 MB (reicht viele Tage)
        _ROTATING_FILE_PATH = _DOTFOLDER / "default.log"
        # TODO use https://pypi.org/project/concurrent-log-handler/ instead of RotatingFileHandler
        # DONE Segmente vergrößern. DWD Tagesload macht 665k Log :)
        _ROTATING_FILE_HANDLER = RotatingFileHandler(_ROTATING_FILE_PATH, maxBytes=1_000_000, backupCount=10)
        _ROTATING_FILE_HANDLER.setLevel(logging.INFO)
        handlers.append(_ROTATING_FILE_HANDLER)
        remark.append("collective")

    if console:
        # console output TODO how can we switch off via ini-file?
        _STDOUT_HANDLER = logging.StreamHandler(sys.stdout)
        _STDOUT_HANDLER.setLevel(logging.DEBUG)
        handlers.append(_STDOUT_HANDLER)
        remark.append("console")

    if process:
        # file for output of the current run, will be sent via mail
        _FILE_PATH = _DOTFOLDER / "current.log"
        _FILE_HANDLER = logging.FileHandler(_FILE_PATH, mode="w")
        _FILE_HANDLER.setLevel(logging.DEBUG)
        handlers.append(_FILE_HANDLER)
        remark.append("process")

    # noinspection PyArgumentList
    logging.basicConfig(level=logging.INFO, handlers=handlers, format=_LOGGING_FMT)
    logging.info(f"LogManager lebt. ({','.join(remark)})")


def _tail(fnam: Path, circa: int = 1500) -> str:
    """
    Quickly get the last few lines of a possibly big log file.
    :param fnam: Path or str to the file
    :param circa: Specify approx. size of tail (from end of file)
    :return: last few lines of the file
    """
    # https://www.roytuts.com/read-last-n-lines-from-file-using-python/
    # https://stackoverflow.com/questions/46258499/read-the-last-line-of-a-file-in-python
    # https://www.openwritings.net/pg/python/python-read-last-line-file
    # https://stackoverflow.com/questions/17615414/how-to-convert-binary-string-to-normal-string-in-python3
    with open(fnam, 'rb') as fh:
        fh.seek(0, os.SEEK_END)
        offset = min(1500, fh.tell())
        fh.seek(-offset, os.SEEK_CUR)
        last_lines = fh.readlines()
        # first line might be incomplete
        if len(last_lines) > 1:
            last_lines = last_lines[1:]
        # decode list of b-strings into str with LFs
        return "...\n" + "".join([ l.decode() for l in last_lines ])


def flag_as_error() -> None:
    """
    When sending the log via mailgun
        a) the prefix will be "ERROR - ", not "SUCCESS - "
        b) the full log of the current run will be sent, rather than only the last few lines
    """
    global ERROR
    ERROR = True


def _shoot_mail(subject="from Johanna with love"):
    global _FILE_HANDLER

    # close current.log
    # https://stackoverflow.com/questions/15435652/python-does-not-release-filehandles-to-logfile
    if not _FILE_HANDLER:
        raise Exception("Cannot send mail without content in process logger.")

    logger = logging.getLogger()
    logger.removeHandler(_FILE_HANDLER)
    _FILE_HANDLER = None
    logging.info(f'closed {_FILE_PATH}')

    # send file contents via email
    # DONE bei SUCCESS nur eine kleine Statistik senden, nur bei ERROR das ganze Log
    if ERROR:
        # https://realpython.com/python-pathlib/#reading-and-writing-files
        body = _FILE_PATH.read_text()
    else:
        body = _tail(_FILE_PATH)

    # logger.addHandler(_FILE_HANDLER) TODO not throw away but append after reading the contents

    subject = ( "ERROR - " if ERROR else "SUCCESS - " ) + subject
    mailgun(subject, body)


def mailgun(subject: str, body: str) -> None:
    url = get("mailgun", "url")
    auth_key = get("mailgun", "auth-key")
    from_ = get("mailgun", "from")
    to = get("mailgun", "to")
    active = url and auth_key and from_ and to

    if not active:
        logging.info(f"no mailgun account configured (subject={subject})")
    else:
        logging.info(f"sending mail: {subject}")
        try:
            r = requests.post(
                url,
                auth=("api", auth_key),
                data={
                    "from": from_,
                    "to": to,
                    "subject": subject,
                    "text": body
                })
            logging.info(f"mailgun: HTTP {r.status_code}")
        except Exception as ex:
            logging.exception(f"mailgun")


class Timer(object):
    """
    Context handler implementation of a stopwatch.
    use like so:
        with Timer() as t:
            sleep(2)
            print(t.read(raw=True))
        print(t.read())
    """
    def __init__(self):
        self.elapsed = None
        pass
    def __enter__(self):
        self.start = perf_counter()
        return self
    def __exit__(self, type, value, traceback):
        self.elapsed = perf_counter() - self.start
    def reset(self):
        self.start = perf_counter()
    def read(self, raw=False):
        if self.elapsed:
            return self.elapsed if raw else "[%0.3f s]" % self.elapsed
        else:
            dt = perf_counter() - self.start
            return dt if raw else "[%0.3f s]" % dt


def ls(path: Path) -> None:
    """
    Listet das angegebene Verzeichnis in zeitlicher Sortierung ins log.
    Cortesy https://linuxhandbook.com/execute-shell-command-python/

    :param path: das zu listende Verzeichnis
    """
    console = os.popen(f'cd {path}; ls -latr').read()
    logging.info(f"ls -la {path}:\n" + console)


# johanna will modify this directly only
GLOBAL_STAT = defaultdict(int)

def collect_stat(collector: str, value_to_add: Union[int, float]) -> None:
    """
    Maintain global statistics values that are logged at the end of the current run.
    :param collector: Name of the collector
    :param value_to_add: Value to aggregate into the statistics
    :return:
    """
    # TODO add memory and runtime info here?
    if collector in [ "connection_sec", ]:
        raise ValueError(f"collector='{collector}' is reserved for johanna internal use")
    GLOBAL_STAT[collector] += value_to_add


class Connection:
    """
    Manages SQLite connection and cursor to avoid caring for the name in many routines.
    Nur als Context Handler verwendbar!
    """

    def __init__(self, text: str ="some activities", dbpath: Union[str, Path] = None):
        # Application will not have to supplay database file name
        if dbpath:
            if isinstance(dbpath, str):
                dbpath = Path(dbpath)
        else:
            dbpath = _DBPATH
        assert isinstance(dbpath, Path)
        self._dbpath = dbpath
        self._text = text

    def __enter__(self):
        """
        cur und con sind public für den Verwender
        """
        self.t0 = perf_counter()
        logging.info(f"Connection to {self._dbpath.name}")
        self.conn = sqlite3.connect(self._dbpath)
        self.cur = self.conn.cursor()
        return self

    def commit(self):
        self.conn.commit()
        # DONE sqlite3.OperationalError: database is locked – der Leseversuch wird von außen wiederholt
        # TODO Retry in die Connection-Klasse einbauen statt im Aufrufer

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        self.cur = None
        self.conn = None
        dt = perf_counter() - self.t0
        GLOBAL_STAT["connection_sec"] += dt
        GLOBAL_STAT["connection_count"] += 1
        logging.info(f"Connection to {self._dbpath.name} was open for {dt:.6f} s ({self._text})")


def apply_schema(schema: Union[str, Path]):
    # TODO support more than one schema per db
    if isinstance(schema, str):
        schema = Path(schema)
    assert isinstance(schema, Path)
    sql = schema.read_text()
    # Neue Tabellen, Indizes und Views können im Fluge angelegt werden
    # Strukturänderungen müssen außerhalb des Tools gelöst erden
    logging.info(f"Applying {schema}")
    with Connection(f"apply {schema}") as c:
        c.cur.executescript(sql)


def main(callback,
         dotfolder: Union[Path, str] = None,
         mail_subject: str = "Johanna",
         dbname: str = "johanna.sqlite"  # set default for Connection context handler
         ):
    global ERROR
    tracemalloc.start()
    pc0 = perf_counter()
    pt0 = process_time()
    _initialize(dotfolder=dotfolder, dbname=dbname)
    try:
        try:
            callback()
            # TODO better formatting for statistics
            logging.info("Statistics: " + json.dumps(GLOBAL_STAT, indent=4))
        except DocoptExit as ex:
            ERROR = True
            logging.exception("DocoptExit")
        except DocoptLanguageError as ex:
            ERROR = True
            logging.exception("DocoptLanguageError")
        logging.info("Time total: %0.1fs (%0.1fs process)" % (perf_counter() - pc0, process_time() - pt0))
        current, peak = tracemalloc.get_traced_memory()
        logging.info("Memory: current = %0.1f MB, peak = %0.1f MB" % (current / 1024.0 / 1024, peak / 1024.0 / 1024))
    except KeyboardInterrupt:
        logging.warning("Caught KeyboardInterrupt")
    except Exception as ex:
        ERROR = True
        logging.exception("Sorry.")
    _shoot_mail(mail_subject)
    logging.info("Ciao.")
    print()
    print()
