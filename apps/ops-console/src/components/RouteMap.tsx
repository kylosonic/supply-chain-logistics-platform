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
    <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <h3 className="mb-4 text-sm font-semibold text-slate-700">Map-based Route Visualization</h3>
      <div className="h-[420px] overflow-hidden rounded">
        <MapContainer center={polyline[0] ?? ADDIS_CENTER} zoom={11} scrollWheelZoom className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
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
          {polyline.length >= 2 ? <Polyline positions={polyline} color="#0f172a" weight={4} /> : null}
        </MapContainer>
      </div>
    </div>
  );
}
