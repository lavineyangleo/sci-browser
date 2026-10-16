using System;
using System.IO;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

namespace SciBrowser.Core {
    public static class PortableConfig {
        public static void Initialize(string root) {
            Directory.CreateDirectory(Path.Combine(root, "config"));
            string service = Path.Combine(root, "services", "mihomo");
            Directory.CreateDirectory(Path.Combine(service, "runtime"));
            var json = new JavaScriptSerializer();
            string path = Path.Combine(service, "settings.json");
            var settings = File.Exists(path)
                ? json.Deserialize<Dictionary<string, object>>(File.ReadAllText(path))
                : new Dictionary<string, object>();
            if (!settings.ContainsKey("token") || string.IsNullOrEmpty(settings["token"] as string)) {
                byte[] bytes = new byte[32];
                using (var random = RandomNumberGenerator.Create()) random.GetBytes(bytes);
                settings["token"] = Convert.ToBase64String(bytes);
            }
            settings["core"] = Path.Combine(service, "core", "mihomo.exe");
            File.WriteAllText(path, json.Serialize(settings), new UTF8Encoding(false));
            string state = Path.Combine(service, "state.json");
            if (!File.Exists(state)) File.WriteAllText(state,
                "{\"enabled\":false,\"profile\":{\"host\":\"\",\"port\":1080,\"username\":\"\",\"password\":\"\"}}", new UTF8Encoding(false));
            File.WriteAllText(Path.Combine(root, "extensions", "sci-proxy", "local-token.js"),
                "export const TOKEN = " + json.Serialize(settings["token"]) + ";\n", new UTF8Encoding(false));
        }
    }
}
