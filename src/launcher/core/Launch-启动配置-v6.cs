using System;
using System.IO;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

namespace SciBrowser.Core {
    public class ProxyConfig {
        public string scheme { get; set; }
        public string host { get; set; }
        public int port { get; set; }
        public string username { get; set; }
        public string password { get; set; }
    }
    public static class LaunchConfig {
        public static string Quote(string value) {
            return "\"" + Regex.Replace(Regex.Replace(value, "(\\\\*)\"", "$1$1\\\""), "(\\\\+)$", "$1$1") + "\"";
        }
        public static string Arguments(string root) {
            string extension = Path.Combine(root, "extensions", "sci-proxy");
            if (!File.Exists(Path.Combine(extension, "manifest.json")))
                throw new Exception("Missing built-in sci-proxy extension.");
            string cookieExtension = Path.Combine(root, "extensions", "web-cookie-skill", "browser-extension");
            if (!File.Exists(Path.Combine(cookieExtension, "manifest.json")))
                throw new Exception("Missing built-in sci-cookie extension.");
            return "--user-data-dir=" + Quote(Path.Combine(root, "profiles", "sci-browser-v5"))
                + " --load-extension=" + Quote(extension + "," + cookieExtension)
                + " --disable-quic --webrtc-ip-policy=disabled --new-window about:blank";
        }

        public static bool IsBrowser(string path, string self) {
            return !string.IsNullOrEmpty(path) && File.Exists(path)
                && string.Equals(Path.GetExtension(path), ".exe", StringComparison.OrdinalIgnoreCase)
                && !string.Equals(Path.GetFullPath(path), Path.GetFullPath(self), StringComparison.OrdinalIgnoreCase);
        }
        public static string FindBrowser(string root, string self) {
            string saved = Path.Combine(root, "config", "browser-path.local.txt");
            string[] candidates = {
                Path.Combine(root, "runtime", "Chrome-bin-v4", "chrome.exe"),
                File.Exists(saved) ? File.ReadAllText(saved).Trim() : "",
                Path.Combine(root, "Chrome-bin", "chrome.exe"),
                Path.GetFullPath(Path.Combine(root, "..", "..", "Chrome-bin", "chrome.exe"))
            };
            foreach (string candidate in candidates) if (IsBrowser(candidate, self)) return candidate;
            return null;
        }
    }
}
