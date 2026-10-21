import L, { type LatLngExpression } from 'leaflet';
import { useMemo } from 'react';
import { MapContainer, Marker, Polygon, Polyline, Popup, TileLayer } from 'react-leaflet';

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

import { Panel } from './ui/Panel';
import type { RouteStop, WeatherRiskZone } from '../types/api';

type Props = {
  stops: RouteStop[];
  riskZones?: WeatherRiskZone[];
};

const ADDIS_CENTER: LatLngExpression = [8.9806, 38.7578];

const defaultIcon = L.icon({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export function RouteMap({ stops, riskZones = [] }: Props) {
  const validStops = useMemo(
    () => stops.filter((s) => typeof s.latitude === 'number' && typeof s.longitude === 'number'),
    [stops],
  );
  const polyline: LatLngExpression[] = validStops.map((s) => [s.latitude as number, s.longitude as number]);

  const totalDistance = validStops.reduce((sum, s) => sum + (s.leg_distance_km ?? 0), 0);
  const totalDemand = validStops.reduce((sum, s) => sum + (s.demand_units ?? 0), 0);

  return (
    <Panel
      eyebrow="Route map"
      title="Spatial route review"
      description="Visual map of the optimized route path with stop markers and distance segments."
    >
      <div className="relative h-[420px] overflow-hidden rounded-xl border border-slate-800/60">
        {validStops.length === 0 ? (
          <div className="absolute inset-0 z-[500] grid place-items-center bg-slate-950/88 text-center text-sm text-slate-400">
            <div className="max-w-xs space-y-3 px-4">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border border-slate-800 bg-slate-900/60">
                <svg className="h-7 w-7 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
                </svg>
              </div>
              <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-50">No mapped stops yet</p>
              <p>Run a route scenario with geocoded warehouse data to preview the path here.</p>
            </div>
          </div>
        ) : null}

        <MapContainer center={polyline[0] ?? ADDIS_CENTER} zoom={11} scrollWheelZoom className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          {validStops.map((stop) => (
            <Marker key={stop.sequence} icon={defaultIcon} position={[stop.latitude as number, stop.longitude as number]}>
              <Popup>
                <div>
                  <p className="font-semibold">
                    #{stop.sequence} {stop.warehouse_code}
                  </p>
                  <p>Demand: {stop.demand_units}</p>
                  <p>Leg: {stop.leg_distance_km} km</p>
                </div>
              </Popup>
            </Marker>
          ))}
          {riskZones.map((zone) => (
            <Polygon
              key={zone.id}
              positions={zone.polygon as LatLngExpression[]}
              pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.3 }}
            >
              <Popup>
                <div className="font-semibold">Weather Risk Zone</div>
                <div className="text-sm">Severity: {zone.severity_score}/10</div>
                <div className="text-xs text-slate-500">
                  {zone.source === 'simulated'
                    ? 'Simulated — not live weather'
                    : zone.source === 'live'
                      ? 'Live provider data'
                      : 'Weather source not declared'}
                </div>
              </Popup>
            </Polygon>
          ))}
          {polyline.length >= 2 ? <Polyline positions={polyline} color="#38bdf8" weight={4} /> : null}
        </MapContainer>
      </div>

      {validStops.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-4">
          <div className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-1.5 text-xs text-slate-300">
            <span className="font-semibold text-slate-100">{validStops.length}</span> stops
          </div>
          <div className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-1.5 text-xs text-slate-300">
            <span className="font-semibold text-slate-100">{totalDistance.toFixed(1)}</span> km total
          </div>
          <div className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-1.5 text-xs text-slate-300">
            <span className="font-semibold text-slate-100">{totalDemand.toLocaleString()}</span> units demand
          </div>
        </div>
      ) : null}
    </Panel>
  );
}

