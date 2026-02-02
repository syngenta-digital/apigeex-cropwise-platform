/**
 * parse-jwt-token.js
 * 
 * Parses JWT token from Authorization header and extracts claims.
 * Sets context variables for use in subsequent policies.
 */

// Get token extracted by EV-Extract-JWT-Token policy
var token = context.getVariable("jwt.token");

if (!token) {
    context.setVariable("jwt.valid", false);
    context.setVariable("jwt.error", "No token provided");
} else {
    try {
        // Split JWT into parts
        var parts = token.split(".");
        
        if (parts.length !== 3) {
            throw new Error("Invalid JWT format");
        }
        
        // Decode payload (base64url)
        var payload = parts[1];
        // Convert base64url to base64
        payload = payload.replace(/-/g, "+").replace(/_/g, "/");
        
        // Pad with '=' if needed
        while (payload.length % 4 !== 0) {
            payload += "=";
        }
        
        // Decode and parse
        var decoded = decodeURIComponent(escape(atob(payload)));
        var claims = JSON.parse(decoded);
        
        // Set standard claims as context variables
        context.setVariable("jwt.valid", true);
        context.setVariable("jwt.sub", claims.sub || "");
        context.setVariable("jwt.username", claims.username || claims.user_name || claims.sub || "");
        context.setVariable("jwt.client_id", claims.client_id || claims.azp || "");
        context.setVariable("jwt.iss", claims.iss || "");
        context.setVariable("jwt.exp", claims.exp || 0);
        context.setVariable("jwt.iat", claims.iat || 0);
        
        // Set optional claims if present
        if (claims.scope) {
            context.setVariable("jwt.scope", claims.scope);
        }
        
        if (claims.roles) {
            context.setVariable("jwt.roles", JSON.stringify(claims.roles));
        }
        
        if (claims.is_using_rbac !== undefined) {
            context.setVariable("jwt.is_using_rbac", claims.is_using_rbac);
        }
        
        // Check expiration
        var now = Math.floor(Date.now() / 1000);
        if (claims.exp && claims.exp < now) {
            context.setVariable("jwt.expired", true);
            context.setVariable("jwt.valid", false);
            context.setVariable("jwt.error", "Token expired");
        } else {
            context.setVariable("jwt.expired", false);
        }
        
        print("[JWT] Parsed token for user: " + (claims.username || claims.user_name || claims.sub));
        
    } catch (e) {
        context.setVariable("jwt.valid", false);
        context.setVariable("jwt.error", "Failed to parse JWT: " + e.message);
        print("[JWT] Parse error: " + e.message);
    }
}
