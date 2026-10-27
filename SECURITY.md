# Security and safety boundaries

Research software only. OFF and SHADOW always return the trusted baseline.
There is no controller write capability, production adapter, external telemetry,
state persistence or vehicle installation procedure.

Report an invariant bypass privately through the repository owner's available
GitHub security reporting channel. If private reporting is unavailable, contact
the owner before publishing sensitive details. Do not attach VINs, routes,
driver identities, images, tokens or raw vehicle logs to issues.

Invalid construction raises ValidationError. Unexpected processing exceptions
are caught at the engine boundary and reported as INTERNAL_ERROR with baseline.
Exception type is recorded without message content. This is not a sandbox for
malicious Python code and does not provide hard real-time deadlines or functional
safety certification. Dependencies and Python execution remain trusted.
