import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vitest/config';
import { playwright } from '@vitest/browser-playwright';
import vercelAdapter from '@sveltejs/adapter-vercel';
import staticAdapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';

const apiProxyTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:7501';

// Two deployments, one build. Vercel keeps its own adapter; the AWS deployment
// serves the same app as prerendered files from S3 behind CloudFront, which
// needs no server at all because every route sets `prerender = true`.
//
// `DEPLOY_TARGET=aws bun run build` produces the S3 upload. The fallback is
// 404.html rather than index.html so that a missing key is a 404 instead of the
// homepage served under the wrong URL.
const adapter =
	process.env.DEPLOY_TARGET === 'aws' ? staticAdapter({ fallback: '404.html' }) : vercelAdapter();

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			adapter
		})
	],
	server: {
		proxy: {
			'/api': {
				target: apiProxyTarget,
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/api/, '')
			}
		}
	},
	test: {
		expect: { requireAssertions: true },
		projects: [
			{
				extends: './vite.config.ts',
				test: {
					name: 'client',
					browser: {
						enabled: true,
						provider: playwright(),
						instances: [{ browser: 'chromium', headless: true }]
					},
					include: ['src/**/*.svelte.{test,spec}.{js,ts}'],
					exclude: ['src/lib/server/**']
				}
			},

			{
				extends: './vite.config.ts',
				test: {
					name: 'server',
					environment: 'node',
					include: ['src/**/*.{test,spec}.{js,ts}'],
					exclude: ['src/**/*.svelte.{test,spec}.{js,ts}']
				}
			}
		]
	}
});
