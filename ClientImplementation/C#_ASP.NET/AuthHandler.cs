using System.Security.Claims;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace FlaskAuthSDK
{
    public class FlaskAuthHandler : AuthenticationHandler<AuthenticationSchemeOptions>
    {
        public FlaskAuthHandler(IOptionsMonitor<AuthenticationSchemeOptions> options,
                                 ILoggerFactory logger,
                                 UrlEncoder encoder,
                                 ISystemClock clock) : base(options, logger, encoder, clock)
        { }

        protected override async Task<AuthenticateResult> HandleAuthenticateAsync()
        {
            var authClient = Context.RequestServices.GetService<FlaskAuthClient>();
            if (authClient is null)
            {
                Console.WriteLine("FlaskAuthClient needs to be setup as a Service for Auth to work!");
                return AuthenticateResult.NoResult(); // Guest user
            }

            bool succes_device_id = Request.Cookies.TryGetValue("device_id", out string? device_id);
            bool succes_hmac_secret = Request.Cookies.TryGetValue("hmac_secret", out string? hmac_secret);

            if (!(succes_device_id && succes_hmac_secret))
            {
                return AuthenticateResult.NoResult(); // Guest user
            }

            (bool success, AuthUserData? user) = await authClient.VerifyClient(device_id, hmac_secret);

            if (!success)
            {
                return AuthenticateResult.Fail("Invalid!");
            }

            var claims = new List<Claim>
        {
            new Claim(ClaimTypes.NameIdentifier, user.UserServiceToken),
            new Claim(ClaimTypes.Role, user.UserRole)
            // Add other claims as needed
        };

            var identity = new ClaimsIdentity(claims, "FlaskAuth");
            var principal = new ClaimsPrincipal(identity);

            // Optionally stash full object in HttpContext.Items
            //Context.Items["CustomUser"] = user;

            var ticket = new AuthenticationTicket(principal, "FlaskAuth");
            return AuthenticateResult.Success(ticket);
        }
    }

}
