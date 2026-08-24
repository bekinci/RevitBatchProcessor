
import clr
import System
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import *

import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()

# NOTE: these only make sense for batch Revit file processing mode.
doc = revit_script_util.GetScriptDocument()
# NOTE: this only makes sense for file-based Revit documents.
revitFilePath = revit_script_util.GetRevitFilePath()

if revit_script_util.IsCloudModel():
    cloudProjectId = revit_script_util.GetCloudProjectId()
    cloudModelId = revit_script_util.GetCloudModelId()

# NOTE: these only make sense for data export mode.
sessionDataFolderPath = revit_script_util.GetSessionDataFolderPath()
dataExportFolderPath = revit_script_util.GetDataExportFolderPath()

# TODO: some real work!
Output()
Output("This task script is running!")

# Optional: make pyRevit libraries available to this task script.
# Requires a local pyRevit installation; the task script keeps running
# without pyRevit support if it cannot be loaded.
try:
    import pyrevit_bootstrap
    from pyrevit import revit, DB, script, output
except Exception as e:
    Output("pyRevit not enabled: " + str(e))

