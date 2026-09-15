<script lang="ts">
	import { resolve } from '$app/paths';
	import SearchBar from '$lib/SearchBar.svelte';
	import { searchStudySpots, type StudySpot } from '$lib/studySpots';

	let query = $state('');
	let activeIndex = $state(-1);
	let selectedSpot = $state<StudySpot | null>(null);
	let loading = $state(true);
	let results = $derived(searchStudySpots(query));

	$effect(() => {
		const timer = window.setTimeout(() => (loading = false), 180);
		return () => window.clearTimeout(timer);
	});

	function updateQuery(value: string) {
		query = value;
		activeIndex = -1;
		selectedSpot = null;
	}

	function select(spot: StudySpot) {
		selectedSpot = spot;
		query = spot.name;
		activeIndex = results.findIndex((result) => result.id === spot.id);
	}

	function navigate(event: KeyboardEvent) {
		if (event.key === 'ArrowDown') {
			event.preventDefault();
			activeIndex = Math.min(activeIndex + 1, results.length - 1);
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			activeIndex = Math.max(activeIndex - 1, 0);
		} else if (event.key === 'Enter' && activeIndex >= 0) {
			event.preventDefault();
			select(results[activeIndex]);
		} else if (event.key === 'Escape') {
			updateQuery('');
		}
	}
</script>

<svelte:head>
	<title>StudySpot</title>
	<meta
		name="description"
		content="Discover cafés and other NYC third places where students can meet and study."
	/>
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
				<p class="eyebrow">NYC third places</p>
				<h1 id="hero-title">Find a place to study together.</h1>
				<p class="description">Explore cafés and public gathering places from NYC Open Data.</p>
			</div>

			<div class="search-area">
				<SearchBar
					{query}
					resultCount={results.length}
					onQueryChange={updateQuery}
					onKeydown={navigate}
				/>

				{#if loading}
					<div class="state-card loading" role="status">Finding great places to study…</div>
				{:else if !query.trim()}
					<div class="state-card empty">
						<p>Start with a name, neighborhood, borough, or university.</p>
						<div class="suggestions">
							<button onclick={() => updateQuery('NYU')}>NYU</button><button
								onclick={() => updateQuery('Brooklyn')}>Brooklyn</button
							><button onclick={() => updateQuery('Greenwich Village')}>Greenwich Village</button>
						</div>
					</div>
				{:else if results.length === 0}
					<div class="state-card empty">
						<strong>No study spots found</strong>
						<p>Try a different neighborhood, borough, or university.</p>
					</div>
				{:else}
					<div class="result-heading">
						<span>{results.length} matching {results.length === 1 ? 'spot' : 'spots'}</span><span
							>Use ↑ ↓ and Enter</span
						>
					</div>
					<ul id="search-results" aria-label="Search results">
						{#each results as spot, index (spot.id)}
							<li>
								<button
									class:active={activeIndex === index}
									onclick={() => select(spot)}
									onmouseenter={() => (activeIndex = index)}
								>
									<span class="place-icon">⌖</span>
									<span
										><strong>{spot.name}</strong><small
											>{spot.category} · {spot.neighborhood}, {spot.borough}</small
										><small>{spot.university}</small></span
									>
								</button>
							</li>
						{/each}
					</ul>
				{/if}

				{#if selectedSpot}
					<p class="selection" role="status">
						Selected: <strong>{selectedSpot.name}</strong> — {selectedSpot.address}
					</p>
				{/if}
			</div>
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

	.search-area {
		width: min(760px, 100%);
		text-align: left;
	}
	.state-card,
	ul {
		margin: 14px 0 0;
		border: 1px solid var(--color-border);
		border-radius: 16px;
		background: white;
		box-shadow: 0 12px 30px rgb(34 34 34 / 8%);
	}
	.state-card {
		padding: 22px;
		color: var(--color-muted);
	}
	.state-card p {
		margin: 0;
	}
	.state-card strong {
		color: var(--color-text);
	}
	.loading {
		display: flex;
		gap: 10px;
		align-items: center;
	}
	.loading::before {
		width: 15px;
		height: 15px;
		border: 2px solid #ffd1da;
		border-top-color: var(--color-brand);
		border-radius: 50%;
		content: '';
		animation: spin 0.8s linear infinite;
	}
	.suggestions {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 14px;
	}
	.suggestions button {
		border: 1px solid var(--color-border);
		border-radius: 999px;
		padding: 7px 11px;
		background: white;
		cursor: pointer;
	}
	.result-heading {
		display: flex;
		justify-content: space-between;
		margin: 17px 4px 8px;
		color: var(--color-muted);
		font-size: 13px;
	}
	ul {
		padding: 6px;
		list-style: none;
	}
	li + li {
		border-top: 1px solid #f0f0f0;
	}
	li button {
		display: grid;
		grid-template-columns: 36px 1fr;
		width: 100%;
		gap: 12px;
		border: 0;
		border-radius: 11px;
		padding: 14px;
		color: inherit;
		background: transparent;
		text-align: left;
		cursor: pointer;
	}
	li button:hover,
	li button.active {
		background: #fff0f3;
	}
	.place-icon {
		display: grid;
		width: 34px;
		height: 34px;
		place-items: center;
		border-radius: 10px;
		color: var(--color-brand);
		background: #fff0f3;
		font-size: 20px;
	}
	li strong,
	li small {
		display: block;
	}
	li small {
		margin-top: 3px;
		color: var(--color-muted);
		font-size: 13px;
	}
	.selection {
		margin: 14px 4px 0;
		color: var(--color-muted);
		font-size: 14px;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
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
		.result-heading {
			gap: 10px;
			font-size: 12px;
		}
	}
</style>
