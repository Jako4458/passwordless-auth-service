using Newtonsoft.Json;

namespace FlaskAuthSDK
{
    public class AuthUserData
    {
        [JsonProperty("UserServiceToken")]
        public string UserServiceToken { get; set; }
        
        [JsonProperty("UserRole")]
        public string UserRole { get; set; }

        public override string ToString()
        {
            return JsonConvert.SerializeObject(this, Formatting.Indented);
        }
    }
}
