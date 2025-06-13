// iOS device mapping
const iosDeviceMapping = new Map([
  ["320x480", "iPhone 4S, 4, 3GS, 3G, 1st gen"],
  ["320x568", "iPhone 5, SE 1st Gen, 5C, 5S"],
  ["375x667", "iPhone SE 2nd Gen, 6, 6S, 7, 8"],
  ["375x812", "iPhone X, XS, 11 Pro, 12 Mini, 13 Mini"],
  ["390x844", "iPhone 13, 13 Pro, 12, 12 Pro"],
  ["414x736", "iPhone 8+"],
  ["414x896", "iPhone 11, XR, XS Max, 11 Pro Max"],
  ["428x926", "iPhone 13 Pro Max, 12 Pro Max"],
  ["476x847", "iPhone 7+, 6+, 6S+"],
  ["744x1133", "iPad Mini 6th Gen"],
  ["768x1024", "iPad Mini (5th Gen), iPad (1-6th Gen), iPad Pro (9.7), iPad Mini (1-4), iPad Air (1-2)"],
  ["810x1080", "iPad 7-9th Gen"],
  ["820x1180", "iPad Air (4th gen)"],
  ["834x1194", "iPad Pro (3rd–5th Gen 11\")"],
  ["834x1112", "iPad Air (3rd gen), iPad Pro (10.5\")"],
  ["1024x1366", "iPad Pro (12.9\", 1st–5th Gen)"]
]);

// Desktop platform mapping
const desktopDeviceMapping = new Map([
  ["Win32", "Windows"],
  ["Linux", "Linux"],
  ["MacIntel", "Mac OS"]
]);

// Detect browser
function getBrowser() {
  const userAgent = window.navigator.userAgent;

  if (userAgent.includes("Edg/")) return "Edge";
  if (userAgent.includes("OPR/") || userAgent.includes("Opera")) return "Opera";
  if (userAgent.includes("Chrome") && !userAgent.includes("Edg/") && !userAgent.includes("OPR/")) return "Chrome";
  if (userAgent.includes("Firefox")) return "Firefox";
  if (userAgent.includes("Safari") && !userAgent.includes("Chrome") && !userAgent.includes("Chromium")) return "Safari";
  if (userAgent.includes("Trident") || userAgent.includes("MSIE")) return "Internet Explorer";

  return "Unknown";
}

// Get Android device name
const getAndroidDeviceName = () => {
  const userAgent = window.navigator.userAgent;
  const androidInfo = userAgent.slice(userAgent.indexOf("Android"));
  const deviceInfo = androidInfo.slice(androidInfo.indexOf("; ") + 2, androidInfo.indexOf(")"));
  if (deviceInfo) {
    return deviceInfo.trim().split(" ")[0];
  }
  return "Android";
};

// Get iOS device name
const getIosDeviceName = () => {
  const screenResolution = `${window.screen.width}x${window.screen.height}`;
  const device = iosDeviceMapping.get(screenResolution);
  return device || "iPhone";
};

// Get desktop device name
const getDesktopDeviceName = () => {
  const platform = navigator?.userAgentData?.platform || navigator?.platform || "unknown";
  const device = desktopDeviceMapping.get(platform) ?? "Unknown";
  return device;
};

// Main logic
let detectedDevice = "";
const browser = getBrowser();

const isMobileDevice = window.navigator.userAgent.toLowerCase().includes("mobi");

if (isMobileDevice) {
  if (window.navigator.userAgent.includes("Android")) {
    detectedDevice = getAndroidDeviceName();
  } else {
    detectedDevice = getIosDeviceName();
  }
} else {
  detectedDevice = getDesktopDeviceName();
}

detectedDevice += ` ${browser}`;

// Debug output (optional)
console.log("User Agent:", navigator.userAgent);
console.log("Detected Resolution:", `${window.screen.width}x${window.screen.height}`);
console.log("Detected Device:", detectedDevice);

// Final result
// You can now use `detectedDevice`

