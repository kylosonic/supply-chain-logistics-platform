import { useEffect, useState } from 'react';
import type { DockAppointment } from '../services/logisticsApi';

interface Props {
  appointments: DockAppointment[];
}

export function DockGanttChart({ appointments }: Props) {
  // Simple visualization logic: assume a 12-hour window from 06:00 to 18:00
  // Each hour is 1/12th of the width.
  const chartStartHour = 6;
  const chartEndHour = 18;
  const totalHours = chartEndHour - chartStartHour;

  const getStyleForTime = (timeStr: string) => {
    const d = new Date(timeStr);
    const hour = d.getHours() + d.getMinutes() / 60;
    
    if (hour < chartStartHour) return { left: '0%', width: '0%' };
    if (hour > chartEndHour) return { left: '100%', width: '0%' };
    
    // Assume an appointment takes 1 hour for visualization
    const leftPct = ((hour - chartStartHour) / totalHours) * 100;
    const widthPct = (1 / totalHours) * 100;
    
    return {
      left: `${leftPct}%`,
      width: `${widthPct}%`,
    };
  };

  return (
    <div className="flex h-full flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">Dock Capacity Schedule</h3>
        <div className="flex gap-2 text-xs">
          <span className="flex items-center gap-1"><div className="h-2 w-2 rounded-full bg-blue-500"></div> Scheduled</span>
          <span className="flex items-center gap-1"><div className="h-2 w-2 rounded-full bg-orange-500"></div> Rescheduled</span>
        </div>
      </div>
      
      <div className="relative flex-1 rounded-xl bg-neutral-100 p-4 dark:bg-neutral-800">
        <div className="absolute top-0 bottom-0 left-0 right-0 flex justify-between px-4">
          {Array.from({ length: totalHours + 1 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center border-l border-neutral-300 dark:border-neutral-700 h-full">
              <span className="text-[10px] text-neutral-500 mt-1">{i + chartStartHour}:00</span>
            </div>
          ))}
        </div>
        
        <div className="relative z-10 mt-6 h-full flex flex-col gap-2 overflow-y-auto">
          {appointments.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-neutral-500">No appointments scheduled</div>
          ) : (
            appointments.map((appt) => {
              const style = getStyleForTime(appt.scheduled_time);
              const isRescheduled = appt.status === 'rescheduled';
              return (
                <div key={appt.id} className="relative h-8 w-full rounded-md bg-white/50 dark:bg-black/20 backdrop-blur-sm">
                  <div
                    className={`absolute h-full rounded-md shadow-sm transition-all flex items-center px-2 text-xs font-medium text-white ${isRescheduled ? 'bg-orange-500/80 border border-orange-500' : 'bg-blue-500/80 border border-blue-500'}`}
                    style={style}
                    title={`Truck: ${appt.truck_id}\nStatus: ${appt.status}\nTime: ${new Date(appt.scheduled_time).toLocaleTimeString()}`}
                  >
                    <span className="truncate">{appt.truck_id}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
