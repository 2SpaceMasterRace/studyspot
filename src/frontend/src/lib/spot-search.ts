export type SpotSearchHit = {
	id: string;
	name: string;
	category: string;
	address: string;
	neighborhood: string;
	borough: string;
	latitude: number;
	longitude: number;
	distance_miles: number | null;
	hours_status: 'open' | 'closed' | 'unknown';
};
