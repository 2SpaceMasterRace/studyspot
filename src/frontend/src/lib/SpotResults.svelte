<script lang="ts">
	import type { SpotSearchHit } from './spot-search';

	type Props = {
		spots: SpotSearchHit[];
		loading: boolean;
		error: string;
		searched: boolean;
	};

	let { spots, loading, error, searched }: Props = $props();

	function distanceLabel(distance: number): string {
		return distance < 0.1 ? '<0.1 mi away' : `${distance.toFixed(1)} mi away`;
	}
</script>

<div class="results" aria-live="polite" aria-busy={loading}>
	{#if loading}
		<p class="message">Finding study spots…</p>
	{:else if error}
		<p class="message error" role="alert">{error}</p>
	{:else if searched}
		<h2>{spots.length} {spots.length === 1 ? 'spot' : 'spots'} shown</h2>
		{#if spots.length === 0}
			<p class="message">No spots match those filters. Try a wider radius or turn off Open now.</p>
		{:else}
			<ul>
				{#each spots as spot (spot.id)}
					<li>
						<div class="spot-heading">
							<h3>{spot.name}</h3>
							{#if spot.distance_miles !== null}
								<span class="distance">{distanceLabel(spot.distance_miles)}</span>
							{/if}
						</div>
						<p class="address">{spot.address} · {spot.neighborhood}, {spot.borough}</p>
						<div class="details">
							<span class="category">{spot.category}</span>
							<span class:open={spot.hours_status === 'open'}>
								{spot.hours_status === 'open'
									? 'Open now'
									: spot.hours_status === 'closed'
										? 'Closed now'
										: 'Hours unknown'}
							</span>
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
</div>

<style>
	.results {
		width: min(760px, 100%);
		text-align: left;
	}

	h2 {
		margin: 0 0 16px;
		font-size: 18px;
		letter-spacing: -0.025em;
	}

	ul {
		display: grid;
		gap: 12px;
		margin: 0;
		padding: 0;
		list-style: none;
	}

	li {
		padding: 20px 22px;
		border: 1px solid var(--color-border);
		border-radius: 16px;
		background: #fff;
	}

	.spot-heading {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 12px;
	}

	h3 {
		margin: 0;
		font-size: 18px;
		letter-spacing: -0.03em;
	}

	.distance {
		flex: none;
		font-size: 13px;
		font-weight: 650;
	}

	.address,
	.message {
		color: var(--color-muted);
	}

	.address {
		margin: 8px 0 12px;
		font-size: 14px;
	}

	.message {
		margin: 0;
		padding: 18px 0;
	}

	.error {
		color: #ad1633;
	}

	.details {
		display: flex;
		gap: 12px;
		font-size: 13px;
		font-weight: 600;
	}

	.category {
		text-transform: capitalize;
	}

	.open {
		color: #126b48;
	}
</style>
