import L, { type LatLngExpression } from 'leaflet';
import { useMemo } from 'react';
import { MapContainer, Marker, Polyline, Popup, TileLayer } from 'react-leaflet';

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

import type { RouteStop } from '../types/api';

type Props = {
  stops: RouteStop[];
};

const ADDIS_CENTER: LatLngExpression = [8.9806, 38.7578];

const defaultIcon = L.icon({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export function RouteMap({ stops }: Props) {
  const validStops = useMemo(
    () => stops.filter((s) => typeof s.latitude === 'number' && typeof s.longitude === 'number'),
    [stops],
  );
  const polyline: LatLngExpression[] = validStops.map((s) => [s.latitude as number, s.longitude as number]);

  return (
    <div className="overflow-hidden rounded-[28px] border border-slate-800/80 bg-slate-950/72 p-5 shadow-[0_24px_80px_rgba(2,12,20,0.3)]">
      <div className="mb-4 space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-300/80">Route map</p>
        <h3 className="font-['Space_Grotesk'] text-lg font-semibold text-slate-50">Spatial route review</h3>
      </div>

      <div className="relative h-[420px] overflow-hidden rounded-[20px] border border-slate-800">
        {validStops.length === 0 ? (
          <div className="absolute inset-0 z-[500] grid place-items-center bg-slate-950/88 text-center text-sm text-slate-400">
            <div className="max-w-xs space-y-2 px-4">
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
          {polyline.length >= 2 ? <Polyline positions={polyline} color="#38bdf8" weight={4} /> : null}
        </MapContainer>
      </div>
    </div>
  );
}
