export type StudySpot = {
	id: string;
	name: string;
	category: string;
	address: string;
	neighborhood: string;
	borough: string;
	latitude: number;
	longitude: number;
	university: string;
};

export const studySpots: StudySpot[] = [
	{
		id: 'cafe-reggio',
		name: 'Caffè Reggio',
		category: 'Café',
		address: '119 MacDougal Street',
		neighborhood: 'Greenwich Village',
		borough: 'Manhattan',
		latitude: 40.7306,
		longitude: -74.0003,
		university: 'New York University'
	},
	{
		id: 'bobst-library',
		name: 'Elmer Holmes Bobst Library',
		category: 'Library',
		address: '70 Washington Square South',
		neighborhood: 'Greenwich Village',
		borough: 'Manhattan',
		latitude: 40.7295,
		longitude: -73.9972,
		university: 'New York University'
	},
	{
		id: 'think-coffee',
		name: 'Think Coffee',
		category: 'Café',
		address: '1 Bleecker Street',
		neighborhood: 'Greenwich Village',
		borough: 'Manhattan',
		latitude: 40.7255,
		longitude: -73.9927,
		university: 'New York University'
	},
	{
		id: 'butler-library',
		name: 'Butler Library',
		category: 'Library',
		address: '535 West 114th Street',
		neighborhood: 'Morningside Heights',
		borough: 'Manhattan',
		latitude: 40.8064,
		longitude: -73.9631,
		university: 'Columbia University'
	},
	{
		id: 'dean-and-deluca',
		name: 'Dear Mama Coffee',
		category: 'Café',
		address: '308 East 109th Street',
		neighborhood: 'East Harlem',
		borough: 'Manhattan',
		latitude: 40.7932,
		longitude: -73.9427,
		university: 'Hunter College'
	},
	{
		id: 'brooklyn-public-library',
		name: 'Brooklyn Public Library',
		category: 'Library',
		address: '10 Grand Army Plaza',
		neighborhood: 'Prospect Heights',
		borough: 'Brooklyn',
		latitude: 40.6727,
		longitude: -73.9689,
		university: 'Pratt Institute'
	},
	{
		id: 'qahwah-house',
		name: 'Qahwah House',
		category: 'Café',
		address: '162 Bedford Avenue',
		neighborhood: 'Williamsburg',
		borough: 'Brooklyn',
		latitude: 40.7187,
		longitude: -73.9581,
		university: 'New York University'
	}
];

const normalize = (value: string) => value.trim().toLocaleLowerCase();

export function searchStudySpots(query: string): StudySpot[] {
	const term = normalize(query);
	if (!term) return studySpots;

	return studySpots
		.map((spot) => {
			const fields: Array<[string, number]> = [
				[spot.name, 0],
				[spot.neighborhood, 1],
				[spot.borough, 2],
				[spot.university, 3]
			];
			const match = fields
				.map(([value, priority]) => ({ value: normalize(value), priority }))
				.filter(({ value }) => value.includes(term))
				.sort(
					(a, b) => a.priority - b.priority || a.value.indexOf(term) - b.value.indexOf(term)
				)[0];

			return match ? { spot, priority: match.priority, position: match.value.indexOf(term) } : null;
		})
		.filter(
			(result): result is { spot: StudySpot; priority: number; position: number } => result !== null
		)
		.sort(
			(a, b) =>
				a.priority - b.priority || a.position - b.position || a.spot.name.localeCompare(b.spot.name)
		)
		.map(({ spot }) => spot);
}
