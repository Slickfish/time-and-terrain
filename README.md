# Time & Terrain

Interactive historical maps: campaigns and journeys told on a relief map, with a playable timeline and sources for every event.

## Exhibits

| Exhibit | Path | Status |
|---|---|---|
| The War for Independence, 1775–1783 | `revolutionary-war/` | Published |
| The Campaigns of Alexander, 336–323 BC | `alexander/` | Published (CesiumJS globe) |
| The Wanderings of Odysseus | `odyssey/` | In preparation |

Each exhibit is a single self-contained `index.html` in its own folder. To update one, replace that file.

### Alexander: enabling terrain (Cesium ion)

`alexander/index.html` runs CesiumJS. Without a token it shows a flat globe with Natural Earth II imagery. To get real terrain and satellite imagery:

1. Create a free Cesium ion account at https://ion.cesium.com (the Community plan is for non-commercial use; check the terms if the exhibit is ever shown commercially).
2. Under **Access Tokens**, create a token with only the `assets:read` scope, limited to the assets used: Cesium World Terrain (asset 1) and Sentinel-2 imagery (asset 3954).
3. Open `alexander/index.html` and paste the token into the line `window.ION_TOKEN = "";` near the top.

The token is visible to anyone who views the page source, which is why it should be restricted to those assets.

## Licences

- **Code**: MIT (see `LICENSE`).
- **Historical data and text** (events, movements, summaries, source notes): CC BY 4.0.
- **Third-party**: three.js (MIT, loaded from jsDelivr); Natural Earth (public domain); EB Garamond and IM Fell fonts (SIL Open Font License, served by Google Fonts).

Sources for each exhibit are listed in its **Sources** panel.
