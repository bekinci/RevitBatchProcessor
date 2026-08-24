#
# Revit Batch Processor
#
# Copyright (c) 2020  Dan Rumery, BVN
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

"""
Makes the pyRevit libraries available to RBP task scripts.

Importing this module bootstraps a local pyRevit installation into the RBP
script host engine so that task scripts can use pyRevit idioms such as::

    from pyrevit import revit, DB, script, output

The pyRevit installation is located under the standard pyRevit install root,
or via the BATCHRVT__PYREVIT_HOME environment variable when the default
location is not used.
"""

import os
import sys

try:
    import __builtin__ as builtins  # IronPython 2
except ImportError:
    import builtins  # IronPython 3 / CPython 3

import revit_script_util

_bootstrapped = False


def _find_pyrevit_home():
    """Return the pyRevit install folder containing the libraries, or None."""
    override = os.environ.get("BATCHRVT__PYREVIT_HOME")
    if override and os.path.isdir(override):
        return override

    program_data = os.environ.get("ProgramData", r"C:\ProgramData")
    pyrevit_root = os.path.join(program_data, "pyRevit")
    if not os.path.isdir(pyrevit_root):
        return None

    # Each subfolder of the install root is a separate pyRevit clone.
    for name in sorted(os.listdir(pyrevit_root)):
        candidate = os.path.join(pyrevit_root, name)
        if os.path.isdir(os.path.join(candidate, "pyrevitlib")):
            return candidate
    return None


def _output(message):
    try:
        revit_script_util.Output(message)
    except Exception:
        pass


def _inject_command_builtins(uiapp):
    """Provide the command-context builtins that pyRevit commands normally receive."""
    builtins.__revit__ = uiapp
    builtins.__commandname__ = "RBPTask"
    builtins.__commandpath__ = os.getcwd()
    builtins.__commandbundle__ = "RBPTask.pushbutton"
    builtins.__commandextension__ = "RBP"
    builtins.__commanduniqueid__ = "RBP.RBPTask"
    builtins.__commandcontrolid__ = "RBPTask"
    builtins.__uibutton__ = None


def _bind_documents():
    """Point pyRevit's active document at the document being processed by RBP."""
    import pyrevit

    class _BatchDocs(object):
        @property
        def doc(self):
            try:
                return revit_script_util.GetScriptDocument()
            except Exception:
                return None

        @property
        def docs(self):
            try:
                return [revit_script_util.GetScriptDocument()]
            except Exception:
                return []

    pyrevit.DOCS = _BatchDocs()


def _route_output():
    """Route pyRevit output to the RBP console."""
    import pyrevit.output as pyrevit_output

    class _RBPOutput(object):
        def __init__(self):
            self.title = None
            self.is_std_output = False

        def print(self, *args, **kwargs):
            _output(" ".join(str(a) for a in args))

        def print_md(self, *args, **kwargs):
            self.print(*args, **kwargs)

        def print_table(self, *args, **kwargs):
            self.print(*args, **kwargs)

        def print_md_table(self, *args, **kwargs):
            self.print(*args, **kwargs)

        def print_image(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            self.print(*args, **kwargs)

        def __getattr__(self, name):
            return lambda *a, **k: None

    pyrevit_output.get_output = lambda: _RBPOutput()


def bootstrap():
    """Locate pyRevit, make its libraries importable, and adapt its context to RBP."""
    global _bootstrapped

    home = _find_pyrevit_home()
    if home is None:
        raise RuntimeError(
            "pyRevit libraries were not found. Install pyRevit under the "
            "standard install root or set BATCHRVT__PYREVIT_HOME.")

    sys.path.insert(0, os.path.join(home, "site-packages"))
    sys.path.insert(0, os.path.join(home, "pyrevitlib"))

    # Importing pyRevit requires the command-context builtins to be present.
    _inject_command_builtins(revit_script_util.GetUIApplication())

    import pyrevit
    _output("pyRevit %s ready for RBP task scripts" % pyrevit.VERSION_STRING)

    _bind_documents()
    _route_output()

    _bootstrapped = True


bootstrap()
