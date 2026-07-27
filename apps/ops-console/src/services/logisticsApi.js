import { api } from './api';
export async function getInventoryOverview() {
    const { data } = await api.get('/inventory/overview');
    return data;
}
export async function getForecast(horizonWeeks = 4) {
    const { data } = await api.post('/forecast/weekly-demand', {
        horizon_weeks: horizonWeeks,
    });
    return data;
}
export async function getRouteSchedules() {
    const { data } = await api.get('/routes/schedules');
    return data;
}
export async function optimizeRoute(payload) {
    const { data } = await api.post('/routes/optimize', payload);
    return data;
}
export async function uploadInventoryCsv(file) {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/ingestion/inventory-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
}
export async function uploadOrdersCsv(file) {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/ingestion/orders-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
}
