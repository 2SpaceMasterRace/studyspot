import { afterEach, expect, test, vi } from 'vitest';
import { render } from 'vitest-browser-svelte';
import Page from '../routes/+page.svelte';

const geolocationDescriptor = Object.getOwnPropertyDescriptor(navigator, 'geolocation');

afterEach(() => {
	vi.unstubAllGlobals();
	if (geolocationDescriptor) {
		Object.defineProperty(navigator, 'geolocation', geolocationDescriptor);
	} else {
		Reflect.deleteProperty(navigator, 'geolocation');
	}
});

test('text, radius, and Open now are sent together when controls change', async () => {
	const requests: Record<string, unknown>[] = [];
	vi.stubGlobal(
		'fetch',
		vi.fn(async (_url: string, options: RequestInit) => {
			requests.push(JSON.parse(options.body as string));
			return Response.json([
				{
					id: 'one',
					name: 'Study Cafe',
					category: 'cafe',
					address: '1 Broadway',
					neighborhood: 'Greenwich Village',
					borough: 'Manhattan',
					latitude: 40.73,
					longitude: -73.99,
					distance_miles: 0.2,
					hours_status: 'open'
				}
			]);
		})
	);
	Object.defineProperty(navigator, 'geolocation', {
		configurable: true,
		value: {
			getCurrentPosition: (success: PositionCallback) =>
				success({ coords: { latitude: 40.73, longitude: -73.99 } } as GeolocationPosition)
		}
	});

	const screen = await render(Page);
	await screen.getByRole('textbox', { name: 'Where' }).fill('coffee');
	await screen.getByRole('button', { name: 'Search' }).click();
	await expect.element(screen.getByText('Study Cafe')).toBeVisible();
	await screen.getByRole('checkbox', { name: 'Open now' }).click();
	const radius = screen.getByRole('combobox', { name: 'Distance from me' });
	await radius.selectOptions('1');
	await expect.element(radius).toHaveValue('1');
	await expect.element(screen.getByText('0.2 mi away')).toBeVisible();

	expect(requests.at(-1)).toMatchObject({
		q: 'coffee',
		latitude: 40.73,
		longitude: -73.99,
		radius_miles: 1,
		open_now: true
	});

	await radius.selectOptions('0');
	await screen.getByRole('checkbox', { name: 'Open now' }).click();
	await expect.element(radius).toHaveValue('0');
	expect(requests.at(-1)).toMatchObject({
		q: 'coffee',
		radius_miles: null,
		open_now: false
	});
});
