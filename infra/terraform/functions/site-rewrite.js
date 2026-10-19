// Maps a clean URL onto the key SvelteKit actually wrote into the bucket.
//
// The AWS build uses adapter-static, and every route is prerendered, so the
// output is plain HTML files rather than an SPA shell. SvelteKit's default
// trailingSlash is 'never', which means it writes:
//
//     /          -> index.html
//     /about     -> about.html
//
// S3 has no notion of a directory index below the root and will not guess the
// extension, so the mapping has to happen here. A request is left alone when its
// last segment already contains a dot, which is how static assets keep their
// real content types and cache headers.
//
// A future route that cannot be prerendered, such as /spots/{id} loading from
// the API, will need the adapter's SPA fallback and a different rule here:
// rewriting to /index.html rather than appending .html.

function handler(event) {
	var request = event.request;
	var uri = request.uri;

	if (uri === '/' || uri.endsWith('/')) {
		request.uri = uri + 'index.html';
		return request;
	}

	var segments = uri.split('/');
	if (segments[segments.length - 1].indexOf('.') === -1) {
		request.uri = uri + '.html';
	}

	return request;
}
