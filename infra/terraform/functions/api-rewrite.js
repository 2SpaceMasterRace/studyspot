// Strips the public /api prefix before the request reaches FastAPI.
//
// This is the CloudFront equivalent of the backend service rewrite in
// vercel.json, and it has to agree with it: the API's routes are /health/live
// and /spots, while the public paths are /api/health/live and /api/spots. Both
// edges therefore remove exactly one leading /api segment.

function handler(event) {
	var request = event.request;

	// Only this behavior's /api/* pattern reaches here, so the prefix is always
	// present. Removing it can leave an empty string, which is not a valid URI.
	request.uri = request.uri.slice(4) || '/';

	return request;
}
