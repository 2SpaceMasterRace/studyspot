<script lang="ts">
	import { resolve } from '$app/paths';
	import SearchBar from '$lib/SearchBar.svelte';
</script>

<svelte:head>
	<title>StudySpot</title>
	<meta name="description" content="Lorem ipsum dolor sit amet." />
</svelte:head>

<div class="page">
	<header>
		<a class="brand" href={resolve('/')} aria-label="StudySpot home">
			<svg viewBox="0 0 32 32" aria-hidden="true">
				<path d="M7 7.5h18v17H7z"></path>
				<path d="M11 12h10M11 16h10M11 20h6"></path>
			</svg>
			<span>StudySpot</span>
		</a>
	</header>

	<main>
		<section aria-labelledby="hero-title">
			<div class="copy">
				<p class="eyebrow">Lorem ipsum dolor</p>
				<h1 id="hero-title">Lorem ipsum dolor sit amet.</h1>
				<p class="description">
					Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt.
				</p>
			</div>

			<SearchBar />
		</section>
	</main>
</div>

<style>
	.page {
		min-height: 100vh;
		padding: 0 24px 24px;
	}

	header,
	main {
		width: min(1180px, 100%);
		margin: 0 auto;
	}

	header {
		display: flex;
		align-items: center;
		height: 76px;
	}

	.brand {
		display: inline-flex;
		align-items: center;
		gap: 9px;
		color: var(--color-brand);
		font-size: 20px;
		font-weight: 750;
		letter-spacing: -0.04em;
	}

	.brand svg {
		width: 30px;
		height: 30px;
		fill: none;
		stroke: currentColor;
		stroke-linecap: round;
		stroke-linejoin: round;
		stroke-width: 2;
	}

	section {
		display: flex;
		min-height: calc(100vh - 100px);
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 48px;
		padding: 72px 48px 128px;
		border-radius: 28px;
		background: #f7f1eb;
		text-align: center;
	}

	.copy {
		max-width: 760px;
	}

	.eyebrow {
		margin: 0 0 16px;
		color: var(--color-brand-hover);
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
	}

	h1 {
		margin: 0;
		font-size: clamp(3.2rem, 7vw, 5.75rem);
		font-weight: 750;
		letter-spacing: -0.07em;
		line-height: 0.96;
	}

	.description {
		max-width: 580px;
		margin: 26px auto 0;
		color: var(--color-muted);
		font-size: 17px;
		line-height: 1.6;
	}

	@media (max-width: 560px) {
		.page {
			padding: 0 15px 15px;
		}

		section {
			min-height: calc(100vh - 91px);
			gap: 36px;
			padding: 56px 16px;
			border-radius: 20px;
		}
	}
</style>
