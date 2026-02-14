#!/usr/bin/env python3
"""Extract essential location data for the map viewer."""

import json

locations = []

with open('ancient.jsonl', 'r') as f:
    for line in f:
        try:
            data = json.loads(line)

            name = data.get('friendly_id', '')
            if not name:
                continue

            # Get coordinates from identifications
            lat, lon = None, None
            place_type = 'unknown'

            if data.get('identifications'):
                ident = data['identifications'][0]
                if ident.get('resolutions'):
                    res = ident['resolutions'][0]
                    lonlat = res.get('lonlat', '')
                    if lonlat and ',' in lonlat:
                        parts = lonlat.split(',')
                        lon = float(parts[0])
                        lat = float(parts[1])
                    place_type = res.get('type', 'unknown')

            if lat is None or lon is None:
                continue

            # Get verses
            verses = []
            for v in data.get('verses', []):
                verses.append(v.get('readable', ''))

            # Get thumbnail if available
            thumbnail = None
            if data.get('media', {}).get('thumbnail'):
                thumb = data['media']['thumbnail']
                thumbnail = {
                    'file': thumb.get('file'),
                    'credit': thumb.get('credit'),
                    'description': thumb.get('description', '').replace('<modern id="', '').replace('</modern>', '').split('">')[0] if '<modern' in thumb.get('description', '') else thumb.get('description', '')
                }

            locations.append({
                'id': data.get('id'),
                'name': name,
                'lat': lat,
                'lon': lon,
                'type': place_type,
                'types': data.get('types', []),
                'verses': verses[:10],  # Limit to first 10 verses
                'thumbnail': thumbnail,
                'url_slug': data.get('url_slug')
            })

        except Exception as e:
            continue

# Sort by name
locations.sort(key=lambda x: x['name'])

print(f"Extracted {len(locations)} locations")

with open('locations.json', 'w') as f:
    json.dump(locations, f, indent=2)

print("Saved to locations.json")
