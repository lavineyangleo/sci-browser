using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Diagnostics;
using System.Threading;
using System.Collections.Generic;
using System.Web.Script.Serialization;

namespace SciBrowser.Core {
    public static class MihomoService {
        static bool Healthy(string token) {
            try {
                var request = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:17896/status");
                request.Proxy = null;
                request.Method = "POST";
                request.ContentType = "application/json";
                request.Headers["X-Bridge-Token"] = token;
                request.Timeout = 1500;
                request.ReadWriteTimeout = 1500;
                request.ContentLength = 2;
                using (var stream = request.GetRequestStream()) { stream.WriteByte(123); stream.WriteByte(125); }
                using (var response = request.GetResponse())
                using (var reader = new StreamReader(response.GetResponseStream())) {
                    var result = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(reader.ReadToEnd());
                    return result.ContainsKey("ok") && (bool)result["ok"];
                }
            } catch { return false; }
        }
        public static void EnsureRunning(string root) {
            string directory = Path.Combine(root, "services", "mihomo");
            var settings = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(File.ReadAllText(Path.Combine(directory, "settings.json")));
            string token = (string)settings["token"];
            if (Healthy(token)) return;
            using (var tcp = new TcpClient()) {
                try { tcp.Connect("127.0.0.1", 17896); }
                catch (SocketException) { }
                if (tcp.Connected) throw new Exception("本地管理端口 17896 已被占用或认证失败，请检查现有 Mihomo 服务。");
            }
            var process = Process.Start(new ProcessStartInfo("py.exe", "-3.12 " + LaunchConfig.Quote(Path.Combine(directory, "bridge", "server.py"))) {
                WorkingDirectory = directory, UseShellExecute = false, CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden
            });
            for (int i = 0; i < 30; i++) {
                if (Healthy(token)) return;
                if (process.HasExited) throw new Exception("Mihomo 本地服务启动失败，请检查 Python 3.12 和代理端口。");
                Thread.Sleep(300);
            }
            throw new Exception("Mihomo 本地服务启动超时。");
        }
    }
}
