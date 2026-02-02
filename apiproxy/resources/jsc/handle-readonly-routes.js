/**
 * handle-readonly-routes.js
 * 
 * Handles read-only route prefixing for specific endpoints.
 * This script determines if a request should be routed to 
 * read-only backend replicas based on the request path and method.
 */

var pathSuffix = context.getVariable("proxy.pathsuffix") || "";
var requestVerb = context.getVariable("request.verb");

// Define read-only routes (GET requests that can be served by read replicas)
var readOnlyPatterns = [
    /^\/v1\/users\/[^\/]+$/,           // GET /v1/users/{id}
    /^\/v1\/data\/[^\/]+$/,            // GET /v1/data/{id}
    /^\/v2\/accounts\/[^\/]+$/,        // GET /v2/accounts/{id}
    /^\/remote-sensing\/v1\/imagery/   // GET /remote-sensing/v1/imagery
];

// Check if this is a read-only request
var isReadOnlyRequest = false;

if (requestVerb === "GET") {
    for (var i = 0; i < readOnlyPatterns.length; i++) {
        if (readOnlyPatterns[i].test(pathSuffix)) {
            isReadOnlyRequest = true;
            break;
        }
    }
}

// Set context variable for conditional flow
context.setVariable("is.readonly.request", isReadOnlyRequest);

// Log for debugging
if (isReadOnlyRequest) {
    print("[ReadOnly] Request " + requestVerb + " " + pathSuffix + " marked as read-only");
}
