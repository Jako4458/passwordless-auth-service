using Microsoft.AspNetCore.Http;
using Newtonsoft.Json;

namespace FlaskAuthSDK
{
    public class FlaskAuthClient
    {
        private readonly HttpClient authClient;
        private readonly string ServiceAuthToken;
        private readonly string serviceName;

        public FlaskAuthClient(string authUri, string serviceName, string spotifyServiceToken)
        {
            this.authClient = new HttpClient() { BaseAddress = new Uri(authUri) };
            this.ServiceAuthToken = spotifyServiceToken;
            this.serviceName = serviceName;
        }

        public async Task<(bool, AuthUserData?)> VerifyClient(string device_id, string hmac_secret)
        {
            var message = new HttpRequestMessage(HttpMethod.Get, $"/verify/{serviceName}");

            message.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", ServiceAuthToken);
            message.Headers.Add("Cookie", $"device_id={device_id}; hmac_secret={hmac_secret}");
            string? responseBody;
            AuthVerifyResponse? verifyRes;
            
            try
            {
                HttpResponseMessage response = await authClient.SendAsync(message);
                if (response is null)
                    return (false, null);
                
                responseBody = await response.Content.ReadAsStringAsync();
                verifyRes = JsonConvert.DeserializeObject<AuthVerifyResponse>(responseBody!);

            } catch (System.Net.Http.HttpRequestException e) 
            {
                Console.WriteLine("SEEMS THAT AUTH SERVER IS NOT RUNNING!"); 
                Console.WriteLine($"AUTH ERROR: {e}"); 
                return (false, null);
            } catch (JsonException e)
            {
                Console.WriteLine("Failed to deserialize AuthVerifyResponse:");
                Console.WriteLine(e);
                return (false, null);
            }

            if (verifyRes?.Ok == false)
                return (false, null);

            return (true, verifyRes!.AuthUserData);
        }

        public async Task<(bool, AuthUserData?)> VerifyClientFromHttpRequest(HttpRequest request)
        {
            bool succes_device_id = request.Cookies.TryGetValue("device_id", out string? device_id);
            bool succes_hmac_secret = request.Cookies.TryGetValue("hmac_secret", out string? hmac_secret);

            if (!(succes_device_id && succes_hmac_secret))
            {
                Console.WriteLine("device_id and/or hmac_secret NOT found!");
                return new(false, null);
            }

            return await VerifyClient(device_id, hmac_secret);
        }

    }

}
