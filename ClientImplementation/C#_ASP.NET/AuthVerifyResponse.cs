using Newtonsoft.Json;
using System;

namespace FlaskAuthSDK
{
    public class AuthVerifyResponse
    {
        [JsonProperty("status code")]
        public int StatusCode { get; set; }

        [JsonProperty("status")]
        public string Status { get; set; }

        [JsonProperty("data")]
        public AuthUserData AuthUserData { get; set; }

        public bool Ok => StatusCode >= 200 && StatusCode < 400;

        public override string ToString()
        {
            return JsonConvert.SerializeObject(this, Formatting.Indented);
        }
    }
}