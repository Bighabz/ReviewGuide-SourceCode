'use client'

import { Calendar, MapPin, Utensils, Info } from 'lucide-react'

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
    <div className="space-y-3 mt-6">
      <h3 className="text-lg font-semibold flex items-center gap-2" style={{ color: 'var(--gpt-text)' }}>
        <Calendar size={20} />
        Your Itinerary
      </h3>
      <div className="space-y-4">
        {days.map((day, idx) => (
          <div key={idx} className="border rounded-lg p-5" style={{ background: 'var(--gpt-assistant-message)', borderColor: 'var(--gpt-border)' }}>
            {/* Day header */}
            <div className="flex items-center justify-between mb-4 pb-3 border-b" style={{ borderColor: 'var(--gpt-border)' }}>
              <div>
                <h4 className="text-xl font-bold" style={{ color: 'var(--gpt-text)' }}>Day {day.day}</h4>
                <p className="text-sm" style={{ color: 'var(--gpt-text-secondary)' }}>{day.date}</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold" style={{ color: 'var(--gpt-text)' }}>{day.title}</p>
              </div>
            </div>

            {/* Activities or time-based schedule */}
            {day.activities && day.activities.length > 0 ? (
              <div className="space-y-3">
                {day.activities.map((activity, actIdx) => {
                  // Handle both string format and object format
                  const isString = typeof activity === 'string'
                  const activityName = isString ? activity : activity.name
                  const activityDescription = isString ? undefined : activity.description
                  const activityTime = isString ? undefined : activity.time

                  return (
                    <div key={actIdx} className="flex gap-3">
                      <div className="flex-shrink-0">
                        <MapPin size={18} className="mt-1" style={{ color: 'var(--gpt-text-secondary)' }} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          {activityTime && (
                            <span className="text-xs px-2 py-0.5 rounded" style={{ background: 'var(--gpt-hover)', color: 'var(--gpt-text)' }}>
                              {activityTime}
                            </span>
                          )}
                          <p className="text-sm" style={{ color: 'var(--gpt-text)' }}>{activityName}</p>
                        </div>
                        {activityDescription && (
                          <p className="text-sm" style={{ color: 'var(--gpt-text-secondary)' }}>{activityDescription}</p>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {day.morning && (
                  <div>
                    <h5 className="font-semibold text-sm mb-2" style={{ color: 'var(--gpt-text)' }}>Morning</h5>
                    <p className="text-sm" style={{ color: 'var(--gpt-text)' }}>{day.morning}</p>
                  </div>
                )}
                {day.afternoon && (
                  <div>
                    <h5 className="font-semibold text-sm mb-2" style={{ color: 'var(--gpt-text)' }}>Afternoon</h5>
                    <p className="text-sm" style={{ color: 'var(--gpt-text)' }}>{day.afternoon}</p>
                  </div>
                )}
                {day.evening && (
                  <div>
                    <h5 className="font-semibold text-sm mb-2" style={{ color: 'var(--gpt-text)' }}>Evening</h5>
                    <p className="text-sm" style={{ color: 'var(--gpt-text)' }}>{day.evening}</p>
                  </div>
                )}
              </div>
            )}

            {/* Meals */}
            {day.meals && (
              <div className="mt-4 pt-4 border-t flex gap-2" style={{ borderColor: 'var(--gpt-border)' }}>
                <Utensils size={16} className="mt-0.5 flex-shrink-0" style={{ color: 'var(--gpt-text-secondary)' }} />
                <div className="flex-1">
                  <p className="text-sm font-medium mb-2" style={{ color: 'var(--gpt-text)' }}>Dining Suggestions</p>
                  {typeof day.meals === 'string' ? (
                    <p className="text-sm" style={{ color: 'var(--gpt-text-secondary)' }}>{day.meals}</p>
                  ) : (
                    <div className="space-y-1.5">
                      {day.meals.breakfast && (
                        <div className="text-sm">
                          <span className="font-medium" style={{ color: 'var(--gpt-text)' }}>Breakfast:</span>{' '}
                          <span style={{ color: 'var(--gpt-text-secondary)' }}>{day.meals.breakfast}</span>
                        </div>
                      )}
                      {day.meals.lunch && (
                        <div className="text-sm">
                          <span className="font-medium" style={{ color: 'var(--gpt-text)' }}>Lunch:</span>{' '}
                          <span style={{ color: 'var(--gpt-text-secondary)' }}>{day.meals.lunch}</span>
                        </div>
                      )}
                      {day.meals.dinner && (
                        <div className="text-sm">
                          <span className="font-medium" style={{ color: 'var(--gpt-text)' }}>Dinner:</span>{' '}
                          <span style={{ color: 'var(--gpt-text-secondary)' }}>{day.meals.dinner}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Notes/Tips */}
            {(day.notes || day.tips) && (
              <div className="mt-3 pt-3 border-t flex gap-2" style={{ borderColor: 'var(--gpt-border)' }}>
                <Info size={16} className="mt-0.5 flex-shrink-0" style={{ color: 'var(--gpt-text-secondary)' }} />
                <div className="flex-1">
                  {day.tips && (
                    <div>
                      <p className="text-sm font-medium mb-1" style={{ color: 'var(--gpt-text)' }}>Tips</p>
                      <p className="text-sm" style={{ color: 'var(--gpt-text-secondary)' }}>{day.tips}</p>
                    </div>
                  )}
                  {day.notes && !day.tips && (
                    <p className="text-sm" style={{ color: 'var(--gpt-text-secondary)' }}>{day.notes}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
