//
// Revit Batch Processor
//
// Copyright (c) 2020  Daniel Rumery, BVN
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//

using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using BatchRvt.ScriptHost.Util;
using MSScripting = Microsoft.Scripting;
using ScriptingHosting = Microsoft.Scripting.Hosting;
using IronPythonHosting = IronPython.Hosting;

namespace BatchRvt.ScriptHost;

public static class ScriptUtil
{
    private const string PYTHON_LIB_ZIP_NAME = "python_34_lib.zip";
    private const string STD_LIB_CACHE_DIR_NAME = "PyStdLib34";
    private const string STD_LIB_CACHE_MARKER_NAME = ".extracted";

    public static void AddPythonStandardLibrary(ScriptingHosting.ScriptScope scope)
    {
        var thisAssembly = typeof(ScriptUtil).Assembly;
        var pythonLibResourceName = thisAssembly.GetManifestResourceNames()
            .Single(name => name.ToLowerInvariant().EndsWith(PYTHON_LIB_ZIP_NAME.ToLowerInvariant()));

        // The IronPython 3 engine cannot import Python 3 package submodules
        // (e.g. encodings.utf_8) from a zip meta-path importer. Extract the
        // embedded stdlib zip to a cached folder and put it on the engine's
        // search paths instead, so packages import reliably.
        var stdLibDir = GetOrExtractStdLibFolder(thisAssembly, pythonLibResourceName);
        if (stdLibDir != null)
        {
            var searchPaths = scope.Engine.GetSearchPaths();
            if (!searchPaths.Contains(stdLibDir)) searchPaths.Add(stdLibDir);
            scope.Engine.SetSearchPaths(searchPaths);
        }
    }

    private static string GetOrExtractStdLibFolder(System.Reflection.Assembly assembly, string resourceName)
    {
        try
        {
            var cacheDir = Path.Combine(Path.GetTempPath(), "BatchRvt", STD_LIB_CACHE_DIR_NAME);
            var markerFile = Path.Combine(cacheDir, STD_LIB_CACHE_MARKER_NAME);

            if (!File.Exists(markerFile))
            {
                if (Directory.Exists(cacheDir)) Directory.Delete(cacheDir, true);
                Directory.CreateDirectory(cacheDir);

                using (var stream = assembly.GetManifestResourceStream(resourceName))
                using (var zip = new ZipArchive(stream, ZipArchiveMode.Read))
                {
                    foreach (var entry in zip.Entries)
                    {
                        if (string.IsNullOrEmpty(entry.Name)) continue;
                        var destinationPath = Path.Combine(cacheDir, entry.FullName);
                        Directory.CreateDirectory(Path.GetDirectoryName(destinationPath));
                        using (var entryStream = entry.Open())
                        using (var destinationStream = new FileStream(destinationPath, FileMode.Create, FileAccess.Write))
                        {
                            entryStream.CopyTo(destinationStream);
                        }
                    }
                }

                File.WriteAllText(markerFile, DateTime.UtcNow.ToString("O"));
            }

            return cacheDir;
        }
        catch
        {
            return null;
        }
    }

    private static void AddVariables(ScriptingHosting.ScriptScope scope,
        IEnumerable<KeyValuePair<string, object>> variables)
    {
        foreach (var kv in variables) scope.SetVariable(kv.Key, kv.Value);
    }

    public static void AddBuiltinVariables(ScriptingHosting.ScriptEngine engine,
        IEnumerable<KeyValuePair<string, object>> variables)
    {
        AddVariables(IronPythonHosting.Python.GetBuiltinModule(engine), variables);
    }

    public static void AddSearchPaths(ScriptingHosting.ScriptEngine engine,
        IEnumerable<string> additionalSearchPaths)
    {
        var searchPaths = engine.GetSearchPaths();

        foreach (var path in additionalSearchPaths) searchPaths.Add(path);

        engine.SetSearchPaths(searchPaths);
    }

    public static ScriptingHosting.ScriptEngine CreatePythonEngine()
    {
        var engineOptions = new Dictionary<string, object>
        {
            { "FullFrames", true }
            /*{ "Debug", true },*/
        };

        var engine = IronPythonHosting.Python.CreateEngine(engineOptions);

        return engine;
    }

    public static ScriptingHosting.ScriptScope CreateMainModule(ScriptingHosting.ScriptEngine engine)
    {
        var mainModuleScope = IronPythonHosting.Python.CreateModule(engine, "__main__");

        return mainModuleScope;
    }

    public static ScriptingHosting.ScriptSource CreateScriptSourceFromFile(
        ScriptingHosting.ScriptEngine engine, string sourceFilePath
    )
    {
        var sourceText = TextFileUtil.ReadAllText(sourceFilePath);

        var scriptSource =
            engine.CreateScriptSourceFromString(sourceText, sourceFilePath, MSScripting.SourceCodeKind.Statements);

        return scriptSource;
    }
}