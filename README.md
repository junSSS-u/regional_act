# regional_act

A Python-based monitoring tool that tracks posts on Bluesky in real-time for specific search terms and calculates regional activity scores across targeted location keywords. The aggregated activity data is generated as standard GeoJSON for easy map visualization.

## Features
- **Real-Time Keyword Monitoring**: Searches Bluesky posts periodically for targeted topics.
- **Geographic Filtering**: Matches post text against a customizable list of target regions.
- **Activity Tracking**: Keeps track of detected post volume within a moving time window (default: 1 hour).
- **GeoJSON Output**: Exports intensity metrics formatted as GeoJSON Features for interactive map integrations (e.g., Mapbox, Leaflet).
- **Secure Configuration**: Uses `.env` files to securely manage authentication credentials.
