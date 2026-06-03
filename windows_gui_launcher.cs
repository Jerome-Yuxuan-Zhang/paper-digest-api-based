using System;
using System.Diagnostics;
using System.IO;

public static class WindowsGuiLauncher
{
    public static void Main()
    {
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string launcher = Path.Combine(baseDir, "gui_launcher.py");
        string srcDir = Path.Combine(baseDir, "src");

        if (!File.Exists(launcher))
        {
            System.Windows.Forms.MessageBox.Show(
                "gui_launcher.py was not found. Please keep this exe in the paper-digest-qwen project root.",
                "Paper Digest Qwen"
            );
            return;
        }

        if (!TryStart("pythonw.exe", launcher, baseDir, srcDir) && !TryStart("python.exe", launcher, baseDir, srcDir))
        {
            System.Windows.Forms.MessageBox.Show(
                "pythonw.exe or python.exe was not found. Please install Python and add it to PATH.",
                "Paper Digest Qwen"
            );
        }
    }

    private static bool TryStart(string pythonExe, string launcher, string baseDir, string srcDir)
    {
        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = "\"" + launcher + "\"",
                WorkingDirectory = baseDir,
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            startInfo.EnvironmentVariables["PYTHONPATH"] = srcDir;
            Process.Start(startInfo);
            return true;
        }
        catch
        {
            return false;
        }
    }
}
