'use client'

import { Calendar, MapPin, Utensils, Info, Clock, CheckCircle } from 'lucide-react'

interface ItineraryDay {
  day: number
  date: string
  title: string
  morning?: string
  afternoon?: string
  evening?: string
  meals?: string | {
    breakfast?: string
    lunch?: string
    dinner?: string
  }
  notes?: string
  tips?: string  // Add tips field
  activities?: Array<{
    name: string
    description?: string
    time?: string
    duration?: string
    best_time?: string
    landmark?: string
    type?: string
  }>
}

interface ItineraryViewProps {
  days: ItineraryDay[]
}

export default function ItineraryView({ days }: ItineraryViewProps) {
  if (!days || days.length === 0) return null

  return (
    <div className="space-y-6 mt-6">
      <div>
        <h3 className="font-serif text-xl text-[var(--text)] flex items-center gap-2">
          <Calendar size={22} strokeWidth={1.5} className="text-[var(--primary)]" />
          Your Itinerary
        </h3>
        <div className="mt-3 h-px bg-gradient-to-r from-transparent via-[var(--border-strong)] to-transparent"></div>
      </div>

      <div className="relative pl-4 sm:pl-8 space-y-10">
        {/* Timeline vertical line */}
        <div className="absolute left-4 sm:left-8 top-4 bottom-4 w-px bg-[var(--border-strong)] opacity-40 transform -translate-x-1/2"></div>

        {days.map((day, idx) => (
          <div key={idx} className="relative">
            {/* Day Bubble Marker */}
            <div className="absolute left-0 sm:left-0 top-0 w-8 h-8 rounded-full bg-[var(--primary)] text-white font-bold flex items-center justify-center transform -translate-x-1/2 shadow-sm z-10 text-sm">
              {day.day}
            </div>

            {/* Content Container */}
            <div className="ml-6 sm:ml-8 bg-[var(--surface-elevated)] border border-[var(--border)] rounded-xl p-5 sm:p-6 shadow-card hover:shadow-card-hover transition-shadow">

              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 pb-4 border-b border-[var(--border)]">
                <div>
                  <h4 className="font-serif text-lg text-[var(--text)]">{day.title}</h4>
                  <p className="text-sm text-[var(--text-muted)] mt-1">{day.date}</p>
                </div>
              </div>

              {/* Activities or time-based schedule */}
              {day.activities && day.activities.length > 0 ? (
                <div className="space-y-6">
                  {day.activities.map((activity, actIdx) => {
                    // Handle both string format and object format
                    const isString = typeof activity === 'string'
                    const activityName = isString ? activity : activity.name
                    const activityDescription = isString ? undefined : activity.description
                    const activityTime = isString ? undefined : activity.time

                    return (
                      <div key={actIdx} className="relative pl-4 border-l-2 border-[var(--border)]">
                        <div className="flex flex-col gap-1">
                          {activityTime && (
                            <span className="text-[11px] font-semibold uppercase tracking-widest text-[var(--primary)] flex items-center gap-1 mb-1">
                              <Clock size={12} strokeWidth={1.5} />
                              {activityTime}
                            </span>
                          )}
                          <p className="text-sm font-semibold text-[var(--text)]">{activityName}</p>
                          {activityDescription && (
                            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{activityDescription}</p>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                // Fallback grid for morning/afternoon/evening
                <div className="grid grid-cols-1 gap-6">
                  {day.morning && (
                    <div className="relative pl-4 border-l-2 border-amber-300">
                      <h5 className="text-[11px] font-semibold uppercase tracking-widest text-[var(--primary)] mb-2">Morning</h5>
                      <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{day.morning}</p>
                    </div>
                  )}
                  {day.afternoon && (
                    <div className="relative pl-4 border-l-2 border-orange-300">
                      <h5 className="text-[11px] font-semibold uppercase tracking-widest text-[var(--primary)] mb-2">Afternoon</h5>
                      <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{day.afternoon}</p>
                    </div>
                  )}
                  {day.evening && (
                    <div className="relative pl-4 border-l-2 border-indigo-300">
                      <h5 className="text-[11px] font-semibold uppercase tracking-widest text-[var(--primary)] mb-2">Evening</h5>
                      <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{day.evening}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Dining Section */}
              {day.meals && (
                <div className="mt-6 pt-6 border-t border-[var(--border)]">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-[var(--surface)] rounded-lg border border-[var(--border)]">
                      <Utensils size={18} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
                    </div>
                    <div className="flex-1">
                      <h5 className="text-sm font-semibold text-[var(--text)] mb-3">Dining</h5>
                      {typeof day.meals === 'string' ? (
                        <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{day.meals}</p>
                      ) : (
                        <div className="grid sm:grid-cols-3 gap-4">
                          {day.meals.breakfast && (
                            <div className="bg-[var(--surface)] p-3 rounded-lg border border-[var(--border)]">
                              <span className="text-[11px] font-semibold uppercase tracking-widest text-[var(--text-muted)] block mb-1">Breakfast</span>
                              <span className="text-sm text-[var(--text)]">{day.meals.breakfast}</span>
                            </div>
                          )}
                          {day.meals.lunch && (
                            <div className="bg-[var(--surface)] p-3 rounded-lg border border-[var(--border)]">
                              <span className="text-[11px] font-semibold uppercase tracking-widest text-[var(--text-muted)] block mb-1">Lunch</span>
                              <span className="text-sm text-[var(--text)]">{day.meals.lunch}</span>
                            </div>
                          )}
                          {day.meals.dinner && (
                            <div className="bg-[var(--surface)] p-3 rounded-lg border border-[var(--border)]">
                              <span className="text-[11px] font-semibold uppercase tracking-widest text-[var(--text-muted)] block mb-1">Dinner</span>
                              <span className="text-sm text-[var(--text)]">{day.meals.dinner}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Tips Section */}
              {(day.notes || day.tips) && (
                <div className="mt-4 pt-4 border-t border-[var(--border)]">
                  <div className="flex gap-3 bg-[var(--primary-light)] border border-[var(--primary)]/10 p-4 rounded-xl">
                    <Info size={20} strokeWidth={1.5} className="text-[var(--primary)] flex-shrink-0 mt-0.5" />
                    <div>
                      {day.tips && (
                        <div className="mb-2 last:mb-0">
                          <p className="text-[11px] font-semibold uppercase tracking-widest text-[var(--primary)] mb-1">Insider Tip</p>
                          <p className="text-sm text-[var(--text)] italic leading-relaxed">{day.tips}</p>
                        </div>
                      )}
                      {day.notes && !day.tips && (
                        <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{day.notes}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
