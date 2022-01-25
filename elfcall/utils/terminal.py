__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"

from subprocess import Popen, PIPE, STDOUT
import os
import re


def colify(listing):
    if len(listing) < 4:
        print("    ".join(listing))
    else:
        for a, b, c, d in zip(
            listing[::4], listing[1::4], listing[2::3], listing[3::4]
        ):
            print("{:<20}{:<20}{:<20}{:<}".format(a, b, c, d))


def iter_split_path(path):
    """
    Given a path (e.g., LD_LIBRARY_PATH or DT_RPATH or DT_RUNPATH split into
    individual paths
    """
    # Semicolon treated the same as :
    path = path.replace(";", ":")
    paths = []
    for path in re.split(":", path):
        if not path:
            paths.append(os.getcwd())
        else:
            paths.append(path)
    return paths


def which(software, strip_newline=True):
    """get_install will return the path to where Singularity (or another
    executable) is installed.
    """
    cmd = ["which", software]
    try:
        result = run_command(cmd)
        if strip_newline is True:
            result["message"] = result["message"].strip("\n")
        return result

    except:  # FileNotFoundError
        return None


def get_installdir():
    """get_installdir returns the installation directory of the application"""
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def run_command(cmd, sudo=False, stream=False):
    """run_command uses subprocess to send a command to the terminal.

    Parameters
    ==========
    cmd: the command to send, should be a list for subprocess
    error_message: the error message to give to user if fails,
    if none specified, will alert that command failed.

    """
    stdout = PIPE if not stream else None
    if sudo is True:
        cmd = ["sudo"] + cmd

    try:
        output = Popen(cmd, stderr=STDOUT, stdout=stdout)

    except FileNotFoundError:
        cmd.pop(0)
        output = Popen(cmd, stderr=STDOUT, stdout=PIPE)

    t = output.communicate()[0], output.returncode
    output = {"message": t[0], "return_code": t[1]}

    if isinstance(output["message"], bytes):
        output["message"] = output["message"].decode("utf-8")

    return output


def confirm_action(question, force=False):
    """confirm if the user wants to perform a certain action

    Parameters
    ==========
    question: the question that will be asked
    force: if the user wants to skip the prompt
    """
    if force is True:
        return True

    response = input(question)
    while len(response) < 1 or response[0].lower().strip() not in "ynyesno":
        response = input("Please answer yes or no: ")

    if response[0].lower().strip() in "no":
        return False

    return True
