using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;
using SciBrowser.Core;
[assembly: System.Reflection.AssemblyTitle("sci-browser")]
[assembly: System.Reflection.AssemblyProduct("sci-browser")]
[assembly: System.Reflection.AssemblyCompany("LavineLeo")]
[assembly: System.Reflection.AssemblyVersion("5.0.0.0")]
namespace SciBrowser.App {
    static class Program {
        [STAThread]
        static int Main(string[] args) {
            string root = AppDomain.CurrentDomain.BaseDirectory;
            bool check = Array.IndexOf(args, "--check") >= 0;
            try {
                PortableConfig.Initialize(root);
                string parameters = LaunchConfig.Arguments(root);
                string browser = LaunchConfig.FindBrowser(root, Application.ExecutablePath);
                if (browser == null && !check) {
                    Application.EnableVisualStyles();
                    using (var picker = new OpenFileDialog()) {
                        picker.Title = "选择支持代理认证的浏览器程序";
                        picker.Filter = "浏览器程序 (*.exe)|*.exe";
                        if (picker.ShowDialog() != DialogResult.OK) return 0;
                        browser = picker.FileName;
                    }
                    if (!LaunchConfig.IsBrowser(browser, Application.ExecutablePath)) throw new Exception("请选择实际浏览器程序，不能选择启动器自身。");
                    File.WriteAllText(Path.Combine(root, "config", "browser-path.local.txt"), browser);
                }
                if (browser == null) throw new Exception("没有找到浏览器程序。");
                if (check) {
                    File.WriteAllText(Path.Combine(root, "config", "launcher-check.local.txt"), "OK\r\nBrowser: " + browser + "\r\nProxy configuration: valid\r\n");
                    return 0;
                }
                MihomoService.EnsureRunning(root);
                Process.Start(new ProcessStartInfo(browser, parameters) { UseShellExecute = false, WorkingDirectory = Path.GetDirectoryName(browser) });
                return 0;
            } catch (Exception e) {
                if (!check) MessageBox.Show(e.Message, "sci-browser 启动失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
        }
    }
}
