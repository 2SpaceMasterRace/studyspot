<script lang="ts">
	import { resolve } from '$app/paths';
	import SearchBar from '$lib/SearchBar.svelte';
	import SpotResults from '$lib/SpotResults.svelte';
	import type { SpotSearchHit } from '$lib/spot-search';

	type Coordinates = { latitude: number; longitude: number };

	let submittedQuery = $state('');
	let radiusMiles = $state(0);
	let openNow = $state(false);
	let coordinates = $state<Coordinates | null>(null);
	let results = $state<SpotSearchHit[]>([]);
	let searched = $state(false);
	let loading = $state(false);
	let locationLoading = $state(false);
	let error = $state('');
	let locationError = $state('');
	let activeRequest: AbortController | null = null;
	let searchSequence = 0;
	let locationSequence = 0;

	async function search(): Promise<void> {
		const sequence = ++searchSequence;
		activeRequest?.abort();
		searched = true;
		results = [];
		error = '';

		if (radiusMiles > 0 && coordinates === null) {
			loading = false;
			return;
		}

		const controller = new AbortController();
		activeRequest = controller;
		loading = true;
		try {
			const response = await fetch('/api/spots/search', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					q: submittedQuery,
					latitude: coordinates?.latitude ?? null,
					longitude: coordinates?.longitude ?? null,
					radius_miles: radiusMiles || null,
					open_now: openNow
				}),
				signal: controller.signal
			});
			if (!response.ok) throw new Error(`Search failed with status ${response.status}`);
			const matches: SpotSearchHit[] = await response.json();
			if (sequence === searchSequence) results = matches;
		} catch (reason) {
			if (
				sequence === searchSequence &&
				!(reason instanceof DOMException && reason.name === 'AbortError')
			) {
				error = 'Search is unavailable. Please try again.';
			}
		} finally {
			if (sequence === searchSequence) loading = false;
		}
	}

	function handleSearch(query: string): void {
		submittedQuery = query;
		void search();
	}

	function handleRadiusChange(event: Event): void {
		radiusMiles = Number((event.currentTarget as HTMLSelectElement).value);
		locationError = '';
		if (radiusMiles === 0) {
			locationSequence++;
			locationLoading = false;
			void search();
			return;
		}
		if (coordinates !== null) {
			void search();
			return;
		}
		activeRequest?.abort();
		searchSequence++;
		results = [];
		loading = false;
		if (!navigator.geolocation) {
			radiusMiles = 0;
			locationError = 'Location is unavailable in this browser. Search continues without a radius.';
			void search();
			return;
		}
		locationLoading = true;
		const sequence = ++locationSequence;
		navigator.geolocation.getCurrentPosition(
			(position) => {
				if (sequence !== locationSequence) return;
				coordinates = {
					latitude: position.coords.latitude,
					longitude: position.coords.longitude
				};
				locationLoading = false;
				void search();
			},
			() => {
				if (sequence !== locationSequence) return;
				radiusMiles = 0;
				locationLoading = false;
				locationError = 'Location access was not granted. Search continues without a radius.';
				void search();
			},
			{ enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
		);
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

	function chooseSuggestion(value: string) {
		updateQuery(value);
		requestAnimationFrame(() => document.getElementById('spot-search')?.focus());
	}

	function select(spot: StudySpot) {
		selectedSpot = spot;
		query = spot.name;
		activeIndex = results.findIndex((result) => result.id === spot.id);
	}

	function navigate(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			updateQuery('');
			return;
		}

		if (!query.trim() || results.length === 0) return;

		if (event.key === 'ArrowDown') {
			event.preventDefault();
			activeIndex = (activeIndex + 1) % results.length;
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			activeIndex = activeIndex <= 0 ? results.length - 1 : activeIndex - 1;
		} else if (event.key === 'Enter') {
			event.preventDefault();
			select(results[activeIndex >= 0 ? activeIndex : 0]);
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
		<section class:showing-results={searched} aria-labelledby="hero-title">
			<div class="copy">
				<h1 id="hero-title">Find a place to study together.</h1>
				<p class="description">Explore cafés and public gathering places from NYC Open Data.</p>
			</div>

			<SearchBar onSearch={handleSearch} />

			<div class="filters" aria-label="Search filters">
				<label class="radius-control" for="radius-filter">
					<span>Distance from me</span>
					<select id="radius-filter" value={String(radiusMiles)} onchange={handleRadiusChange}>
						<option value="0">Any distance</option>
						<option value="0.5">Within ½ mile</option>
						<option value="1">Within 1 mile</option>
						<option value="3">Within 3 miles</option>
						<option value="5">Within 5 miles</option>
					</select>
				</label>
				<label class="open-control">
					<input
						type="checkbox"
						checked={openNow}
						onchange={(event) => {
							openNow = event.currentTarget.checked;
							void search();
						}}
					/>
					<span>Open now</span>
				</label>
			</div>
			{#if locationLoading}
				<p class="filter-note" role="status">Getting your location…</p>
			{:else if locationError}
				<p class="filter-note error" role="alert">{locationError}</p>
			{:else if coordinates !== null}
				<p class="filter-note">Distances are straight-line estimates from your location.</p>
			{/if}

			<SpotResults spots={results} {loading} {error} {searched} />
			<p class="attribution">
				Opening-hours data © <a href="https://www.openstreetmap.org/copyright"
					>OpenStreetMap contributors</a
				>
				under the Open Database License. Hours can change; check with the venue before visiting.
			</p>
			<div class="search-area">
				<SearchBar
					{query}
					resultCount={query.trim() ? results.length : 0}
					activeDescendant={activeIndex >= 0 ? `search-result-${results[activeIndex]?.id}` : ''}
					onQueryChange={updateQuery}
					onKeydown={navigate}
				/>

				{#if loading}
					<div class="state-card loading" role="status">Finding great places to study…</div>
				{:else if !query.trim()}
					<div class="empty-state">
						<div class="empty-icon" aria-hidden="true"><span>⌁</span></div>
						<div>
							<p class="empty-kicker">QUICK DISCOVERY</p>
						</div>
						<div class="suggestions" aria-label="Suggested searches">
							<button
								type="button"
								aria-label="Search by university: NYU"
								onclick={() => chooseSuggestion('NYU')}>NYU</button
							>
							<button
								type="button"
								aria-label="Search by university: Columbia"
								onclick={() => chooseSuggestion('Columbia')}>Columbia</button
							>
							<button
								type="button"
								aria-label="Search by borough: Brooklyn"
								onclick={() => chooseSuggestion('Brooklyn')}>Brooklyn</button
							>
							<button
								type="button"
								aria-label="Search by borough: Manhattan"
								onclick={() => chooseSuggestion('Manhattan')}>Manhattan</button
							>
							<button
								type="button"
								aria-label="Search by neighborhood: Greenwich Village"
								onclick={() => chooseSuggestion('Greenwich Village')}>Greenwich Village</button
							>
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
					<ul id="search-results" role="listbox" aria-label="Search results">
						{#each results as spot, index (spot.id)}
							<li>
								<button
									id={`search-result-${spot.id}`}
									role="option"
									aria-selected={activeIndex === index}
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

	section.showing-results {
		justify-content: flex-start;
		gap: 26px;
	}

	.copy {
		max-width: 760px;
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
	.empty-state {
		display: grid;
		grid-template-columns: auto 1fr;
		align-items: center;
		gap: 13px;
		margin-top: 14px;
		padding: 18px 20px;
		position: relative;
		overflow: hidden;
		border: 1px solid rgb(255 56 92 / 13%);
		border-radius: 16px;
		background: rgb(255 255 255 / 68%);
		box-shadow: 0 12px 30px rgb(34 34 34 / 5%);
	}
	.empty-state::after {
		position: absolute;
		top: -58px;
		right: -38px;
		width: 134px;
		height: 134px;
		border-radius: 50%;
		background: rgb(255 56 92 / 6%);
		content: '';
		pointer-events: none;
	}
	.empty-state > * {
		position: relative;
		z-index: 1;
	}
	.empty-icon {
		display: grid;
		width: 38px;
		height: 38px;
		place-items: center;
		border-radius: 12px;
		color: var(--color-brand);
		background: #fff0f3;
		font-size: 26px;
		line-height: 1;
	}
	.empty-icon span {
		display: block;
		transform: rotate(90deg);
	}
	.empty-kicker {
		margin: 0 0 4px;
		color: var(--color-brand-hover);
		font-size: 12px;
		font-weight: 750;
		letter-spacing: 0.1em;
	}
	.suggestions {
		grid-column: 1 / -1;
		display: flex;
		flex-wrap: wrap;
		gap: 9px;
		margin-top: 2px;
	}
	.suggestions button {
		display: inline-flex;
		align-items: center;
		border: 1px solid #e6d8da;
		border-radius: 999px;
		padding: 8px 13px;
		color: var(--color-text);
		background: #fff;
		font-size: 13px;
		cursor: pointer;
		transition:
			transform 150ms ease,
			border-color 150ms ease,
			background 150ms ease;
	}
	.suggestions button:hover {
		border-color: #ff9bae;
		background: #fff6f7;
		transform: translateY(-1px);
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

	.filters {
		display: flex;
		width: min(760px, 100%);
		align-items: end;
		justify-content: space-between;
		gap: 16px;
		text-align: left;
	}

	.radius-control {
		display: grid;
		gap: 7px;
		font-size: 13px;
		font-weight: 700;
	}

	select {
		min-height: 42px;
		padding: 0 12px;
		border: 1px solid var(--color-border);
		border-radius: 12px;
		background: white;
		color: var(--color-text);
		cursor: pointer;
	}

	.open-control {
		display: flex;
		min-height: 42px;
		align-items: center;
		gap: 8px;
		font-size: 14px;
		font-weight: 700;
		cursor: pointer;
	}

	.open-control input {
		width: 17px;
		height: 17px;
		accent-color: var(--color-brand);
	}

	.filter-note {
		width: min(760px, 100%);
		margin: -12px 0 0;
		color: var(--color-muted);
		font-size: 12px;
		text-align: left;
	}

	.filter-note.error {
		color: #ad1633;
	}

	.attribution {
		width: min(760px, 100%);
		margin: 8px 0 0;
		color: var(--color-muted);
		font-size: 12px;
		line-height: 1.5;
		text-align: left;
	}

	.attribution a {
		text-decoration: underline;
		text-underline-offset: 2px;
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

		.filters {
			align-items: flex-start;
			flex-direction: column;
			gap: 10px;
		.result-heading {
			gap: 10px;
			font-size: 12px;
		}
		.empty-state {
			align-items: start;
			padding: 17px;
		}
	}
</style>
