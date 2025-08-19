# FlaskAuth SDK (ASP.NET Core)

## Overview
The **FlaskAuth SDK** provides simple authentication integration for ASP.NET Core applications. It handles token verification, user data retrieval, and secure middleware integration with your FlaskAuth service.

It works seamlessly with ASP.NET Core’s `[Authorize]` and `[AllowAnonymous]` attributes.

## Features
- Middleware-based authentication handler (`FlaskAuthHandler`)
- Strongly typed models: `AuthUserData`, `AuthVerifyResponse`
- Token/cookie verification via `FlaskAuthClient`
- Integrates with `[Authorize]` and `[AllowAnonymous]`
- Emits standard claims (`NameIdentifier`, `Role`) for policy-based auth

## Requirements
- .NET 8.0 (TargetFramework: `net8.0`)
- Packages (from the project file):
  - `Microsoft.AspNetCore.Authentication.Abstractions`
  - `Microsoft.AspNetCore.Authentication.Cookies`
  - `Microsoft.AspNetCore.Http`
  - `Microsoft.Extensions.Logging` (9.0.6)
  - `Newtonsoft.Json` (13.0.3)

## Installation (Local Project Reference)
This package is **not** on NuGet. Include it manually in your solution:

1. Place the SDK in a `libs/` folder inside your solution (e.g. `libs/FlaskAuthSDK/`).
2. Edit your app’s `.csproj` to reference it:

```xml
<ItemGroup>
  <ProjectReference Include="libs/FlaskAuthSDK/FlaskAuthSDK.csproj" />
</ItemGroup>
```

3. Rebuild your solution:

```sh
dotnet build
```

## Configuration

**appsettings.json** (adjust to your environment):

```json
{
  "FlaskAuth": {
    "BaseUrl": "https://auth.example.com/",
    "ServiceName": "my-service",
    "ServiceToken": "YOUR_SERVICE_TOKEN"
  }
}
```

**Program.cs** — register the client and the custom authentication scheme:

```csharp
using FlaskAuthSDK;
using Microsoft.AspNetCore.Authentication;

var builder = WebApplication.CreateBuilder(args);

// Bind config
var authSection = builder.Configuration.GetSection("FlaskAuth");
var baseUrl = authSection["BaseUrl"] ?? "https://auth.example.com/";
var serviceName = authSection["ServiceName"] ?? "my-service";
var serviceToken = authSection["ServiceToken"] ?? "YOUR_SERVICE_TOKEN";

// Register FlaskAuthClient
builder.Services.AddSingleton(sp =>
    new FlaskAuthClient(baseUrl, serviceName, serviceToken));

// Add Authentication with custom scheme (FlaskAuthHandler lives in this SDK)
builder.Services
    .AddAuthentication(options =>
    {
        options.DefaultAuthenticateScheme = "FlaskAuth";
        options.DefaultChallengeScheme = "FlaskAuth";
    })
    .AddScheme<AuthenticationSchemeOptions, FlaskAuthHandler>("FlaskAuth", _ => { });

builder.Services.AddAuthorization();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/", () => "OK");
app.Run();
```

## Usage

### Protect endpoints with attributes
Controllers or minimal APIs can use `[Authorize]` and `[AllowAnonymous]`:

```csharp
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using FlaskAuthSDK;

[ApiController]
[Route("api/[controller]")]
public class AccountController : ControllerBase
{
    [HttpGet("me")]
    [Authorize] // uses the "FlaskAuth" scheme
    public IActionResult GetProfile()
    {
        var id = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
        var role = User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value;
        return Ok(new { id, role });
    }

    [HttpGet("public")]
    [AllowAnonymous]
    public IActionResult PublicInfo()
    {
        return Ok("This endpoint is open.");
    }
}
```

If you prefer explicit scheme usage:

```csharp
[Authorize(AuthenticationSchemes = "FlaskAuth")]
```

### Accessing claims
`FlaskAuthHandler` issues claims based on verified user data:

- `ClaimTypes.NameIdentifier` → `AuthUserData.UserServiceToken`
- `ClaimTypes.Role` → `AuthUserData.UserRole`

### Cookie-based verification
`FlaskAuthClient` looks for the following cookies (handled in both the handler and the client helper):
- `device_id`
- `hmac_secret`

If either cookie is missing, authentication returns `NoResult` (guest). When present, the client verifies them with the FlaskAuth service.

### Direct client usage
You can inject and use `FlaskAuthClient` in application code (e.g., from an MVC controller or service):

```csharp
using FlaskAuthSDK;

public class SomeService
{
    private readonly FlaskAuthClient _client;
    public SomeService(FlaskAuthClient client) => _client = client;

    public async Task<bool> IsValidAsync(HttpRequest request)
    {
        // Helper reads cookies and validates via the auth server
        var (ok, user) = await _client.VerifyClientFromHttpRequest(request);
        return ok;
    }
}
```

## Models

### `AuthUserData`
```csharp
using Newtonsoft.Json;

public class AuthUserData
{
    [JsonProperty("UserServiceToken")]
    public string UserServiceToken { get; set; }

    [JsonProperty("UserRole")]
    public string UserRole { get; set; }

    public override string ToString() =>
        Newtonsoft.Json.JsonConvert.SerializeObject(this, Newtonsoft.Json.Formatting.Indented);
}
```

### `AuthVerifyResponse`
```csharp
using Newtonsoft.Json;

public class AuthVerifyResponse
{
    [JsonProperty("status code")]
    public int StatusCode { get; set; }

    [JsonProperty("status")]
    public string Status { get; set; }

    [JsonProperty("data")]
    public AuthUserData AuthUserData { get; set; }

    public bool Ok => StatusCode >= 200 && StatusCode < 400;

    public override string ToString() =>
        Newtonsoft.Json.JsonConvert.SerializeObject(this, Newtonsoft.Json.Formatting.Indented);
}
```

## Project Structure

```
├── AuthHandler.cs            # Custom ASP.NET authentication handler (class: FlaskAuthHandler)
├── AuthUserData.cs           # User model; provides UserServiceToken and UserRole
├── AuthVerifyResponse.cs     # Verification response model; includes Ok convenience property
├── FlaskAuthClient.cs        # SDK client for the auth server; reads cookies and verifies
├── FlaskAuthSDK.csproj       # Project configuration (TargetFramework net8.0)
└── README.md                 # This documentation
```

## Versioning (from `FlaskAuthSDK.csproj`)
- `Version`: 1.2.0  
- `AssemblyVersion`: 1.2.0.0  
- `FileVersion`: 1.2.0.0  
- `InformationalVersion`: 1.2.0-beta

## Notes
- The authentication scheme name in examples is `"FlaskAuth"`. If you change it, update `DefaultAuthenticateScheme`, `DefaultChallengeScheme`, and any `[Authorize(AuthenticationSchemes = "...")]` attributes accordingly.
- Ensure your FlaskAuth service URL and service token are correct and reachable from your app.
