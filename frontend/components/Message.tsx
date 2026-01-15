'use client'

import { User, Bot, Copy, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Message as MessageType, NextSuggestion } from './ChatContainer'
import ProductCarousel from './ProductCarousel'
import ProductCards from './ProductCards'
import ProductReview from './ProductReview'
import ProductRecommendations from './ProductRecommendations'
import AffiliateLinks from './AffiliateLinks'
import HotelCards from './HotelCards'
import FlightCards from './FlightCards'
import ItineraryView from './ItineraryView'
import ComparisonTable from './ComparisonTable'
import ListBlock from './ListBlock'
import DestinationInfo from './DestinationInfo'
import { useState, useEffect } from 'react'
import { formatTimestamp, formatFullTimestamp, SUGGESTION_CLICK_PREFIX } from '@/lib/utils'

interface MessageProps {
  message: MessageType
}

export default function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)
  const [relativeTime, setRelativeTime] = useState(() => formatTimestamp(message.timestamp))

  // Update relative timestamp every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setRelativeTime(formatTimestamp(message.timestamp))
    }, 60000) // Update every minute

    return () => clearInterval(interval)
  }, [message.timestamp])

  const handleCopy = async () => {
    try {
      // Try modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(message.content)
      } else {
        // Fallback for non-HTTPS or older browsers
        const textArea = document.createElement('textarea')
        textArea.value = message.content
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        try {
          document.execCommand('copy')
        } finally {
          document.body.removeChild(textArea)
        }
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }

  // Separate carousel and product cards rendering
  const renderCarousels = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    const carousels = message.ui_blocks.filter(block => block.block_type === 'carousel')
    if (carousels.length === 0) return null

    return (
      <div className="space-y-4 mb-4">
        {carousels.map((block, idx) => (
          <ProductCarousel key={idx} items={block.payload?.items || []} />
        ))}
      </div>
    )
  }

  // Render provider-specific product carousels (ebay_products, amazon_products, etc.)
  const renderProviderCarousels = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    // Find all provider-specific product blocks (type ends with "_products" but not just "products")
    const providerBlocks = message.ui_blocks.filter(block =>
      block.type && block.type.endsWith('_products') && block.type !== 'products'
    )
    if (providerBlocks.length === 0) return null

    return (
      <div className="space-y-4 mb-4">
        {providerBlocks.map((block, idx) => {
          // Map provider data format to carousel format
          const carouselItems = (block.data || []).map((product: any) => ({
            product_id: product.product_id || product.id,
            title: product.title || product.name,
            price: product.price,
            currency: product.currency || 'USD',
            affiliate_link: product.url,
            merchant: product.merchant,
            image_url: product.image_url,
            rating: product.rating,
            review_count: product.review_count,
            source: product.source
          }))

          return (
            <ProductCarousel
              key={idx}
              items={carouselItems}
              title={block.title}
            />
          )
        })}
      </div>
    )
  }

  const renderNewFormatProducts = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    // Handle new format: type: "products" with data array (Our Recommendations)
    const newFormatProducts = message.ui_blocks.filter(block => block.type === 'products')
    if (newFormatProducts.length === 0) return null

    return (
      <div className="space-y-4">
        {newFormatProducts.map((block, idx) => {
          // Map new format to carousel format
          const carouselItems = (block.data || []).map((product: any) => ({
            product_id: product.id || product.product_id,
            title: product.name || product.title,
            price: product.best_offer?.price || product.price,
            currency: product.best_offer?.currency || product.currency || 'USD',
            affiliate_link: product.best_offer?.url || product.url,
            merchant: product.best_offer?.merchant || product.merchant,
            image_url: product.best_offer?.image_url || product.image_url,
            rating: product.best_offer?.rating || product.rating,
            review_count: product.best_offer?.review_count || product.review_count
          }))

          return (
            <ProductCarousel
              key={idx}
              items={carouselItems}
              title={block.title}
            />
          )
        })}
      </div>
    )
  }

  const renderProductCards = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    // Handle old format: block_type: "product_cards" with payload.products
    const productCards = message.ui_blocks.filter(block => block.block_type === 'product_cards')
    if (productCards.length === 0) return null

    return (
      <div className="space-y-4 mt-4 w-full sm:max-w-[85%]">
        {productCards.map((block, idx) => (
          <ProductCards key={idx} products={block.payload?.products || []} />
        ))}
      </div>
    )
  }

  const renderProductReviews = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    const productReviews = message.ui_blocks.filter(block => block.block_type === 'product_review')
    if (productReviews.length === 0) return null

    return (
      <div className="space-y-6 mt-6 w-full sm:max-w-[85%]">
        {productReviews.map((block, idx) => (
          <ProductReview key={idx} product={block.payload || {}} />
        ))}
      </div>
    )
  }

  const renderProductRecommendations = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    // Support both old format (block_type) and new format (type)
    const recommendations = message.ui_blocks.filter(block =>
      block.block_type === 'product_recommendations' || block.type === 'product_recommendations'
    )
    if (recommendations.length === 0) return null

    return (
      <div className="space-y-4 mt-4 w-full sm:max-w-[85%]">
        {recommendations.map((block, idx) => (
          <ProductRecommendations key={idx} content={block.payload?.content || block.data?.content || ''} />
        ))}
      </div>
    )
  }

  const renderAffiliateLinks = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    const affiliateBlocks = message.ui_blocks.filter(block => block.block_type === 'affiliate_links')
    if (affiliateBlocks.length === 0) return null

    return (
      <div className="space-y-4 mt-4 w-full sm:max-w-[85%]">
        {affiliateBlocks.map((block, idx) => (
          <AffiliateLinks
            key={idx}
            productName={block.payload?.product_name || ''}
            affiliateLinks={block.payload?.affiliate_links || []}
            rank={block.payload?.rank}
          />
        ))}
      </div>
    )
  }

  const renderHotelCards = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    // Support both old format (block_type: 'hotel_cards', payload.hotels) and new format (type: 'hotels', data)
    const hotelBlocks = message.ui_blocks.filter(block =>
      block.block_type === 'hotel_cards' || block.type === 'hotels'
    )
    if (hotelBlocks.length === 0) return null

    return (
      <div className="space-y-4 mt-4 w-full sm:max-w-[85%]">
        {hotelBlocks.map((block, idx) => (
          <HotelCards key={idx} hotels={block.payload?.hotels || block.data || []} />
        ))}
      </div>
    )
  }

  const renderFlightCards = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    // Support both old format (block_type: 'flight_cards', payload.flights) and new format (type: 'flights', data)
    const flightBlocks = message.ui_blocks.filter(block =>
      block.block_type === 'flight_cards' || block.type === 'flights'
    )
    if (flightBlocks.length === 0) return null

    return (
      <div className="space-y-4 mt-4 w-full sm:max-w-[85%]">
        {flightBlocks.map((block, idx) => (
          <FlightCards key={idx} flights={block.payload?.flights || block.data || []} />
        ))}
      </div>
    )
  }

  // Render hotels and flights side by side on desktop
  const renderTravelCards = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    const hotelBlocks = message.ui_blocks.filter(block =>
      block.block_type === 'hotel_cards' || block.type === 'hotels'
    )
    const flightBlocks = message.ui_blocks.filter(block =>
      block.block_type === 'flight_cards' || block.type === 'flights'
    )

    const hasHotels = hotelBlocks.length > 0
    const hasFlights = flightBlocks.length > 0

    if (!hasHotels && !hasFlights) return null

    // If both hotels and flights exist, render side by side on desktop
    if (hasHotels && hasFlights) {
      return (
        <div className="mt-4 w-full">
          {/* Desktop: side by side grid with equal height */}
          <div className="hidden md:grid md:grid-cols-2 gap-4 items-stretch">
            <div className="flex flex-col">
              {hotelBlocks.map((block, idx) => (
                <HotelCards key={`hotel-${idx}`} hotels={block.payload?.hotels || block.data || []} fullHeight />
              ))}
            </div>
            <div className="flex flex-col">
              {flightBlocks.map((block, idx) => (
                <FlightCards key={`flight-${idx}`} flights={block.payload?.flights || block.data || []} fullHeight />
              ))}
            </div>
          </div>
          {/* Mobile: stacked vertically */}
          <div className="md:hidden space-y-4">
            {hotelBlocks.map((block, idx) => (
              <HotelCards key={`hotel-mobile-${idx}`} hotels={block.payload?.hotels || block.data || []} />
            ))}
            {flightBlocks.map((block, idx) => (
              <FlightCards key={`flight-mobile-${idx}`} flights={block.payload?.flights || block.data || []} />
            ))}
          </div>
        </div>
      )
    }

    // If only one type exists, render normally
    return (
      <div className="mt-4 w-full sm:max-w-[85%]">
        {hasHotels && hotelBlocks.map((block, idx) => (
          <HotelCards key={`hotel-${idx}`} hotels={block.payload?.hotels || block.data || []} />
        ))}
        {hasFlights && flightBlocks.map((block, idx) => (
          <FlightCards key={`flight-${idx}`} flights={block.payload?.flights || block.data || []} />
        ))}
      </div>
    )
  }

  const renderItinerary = () => {
    // Check for itinerary in ui_blocks first
    if (message.ui_blocks && message.ui_blocks.length > 0) {
      // Support both old format (block_type: 'itinerary', payload.days) and new format (type: 'itinerary', data)
      const itineraryBlocks = message.ui_blocks.filter(block =>
        block.block_type === 'itinerary' || block.type === 'itinerary'
      )
      if (itineraryBlocks.length > 0) {
        return (
          <div className="space-y-4 mt-4 w-full sm:max-w-[85%]">
            {itineraryBlocks.map((block, idx) => (
              <ItineraryView key={idx} days={block.payload?.days || block.data || []} />
            ))}
          </div>
        )
      }
    }

    // Check for itinerary as direct field (new format for travel flow)
    if (message.itinerary && message.itinerary.length > 0) {
      return (
        <div className="space-y-4 mt-4 w-full sm:max-w-[85%]">
          <ItineraryView days={message.itinerary} />
        </div>
      )
    }

    return null
  }

  const renderComparisonTable = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    // Support both old format (product_comparison) and new format (comparison_html)
    const comparisonBlocks = message.ui_blocks.filter(block =>
      block.type === 'product_comparison' || block.type === 'comparison_html'
    )
    if (comparisonBlocks.length === 0) return null

    return (
      <div className="space-y-4 mb-4 w-full">
        {comparisonBlocks.map((block, idx) => {
          // New format: comparison_html with HTML content
          if (block.type === 'comparison_html' && block.data?.html) {
            return (
              <div
                key={idx}
                className="comparison-html-container rounded-xl overflow-hidden"
                style={{
                  background: 'var(--gpt-assistant-message)',
                  border: '1px solid rgba(0,0,0,0.08)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                }}
                dangerouslySetInnerHTML={{ __html: block.data.html }}
              />
            )
          }
          // Old format: product_comparison with structured data
          return (
            <ComparisonTable
              key={idx}
              data={block.data}
              title={block.title}
            />
          )
        })}
      </div>
    )
  }

  const renderDestinationFacts = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    const activitiesBlocks = message.ui_blocks.filter(block => block.type === 'activities')
    const attractionsBlocks = message.ui_blocks.filter(block => block.type === 'attractions')
    const restaurantsBlocks = message.ui_blocks.filter(block => block.type === 'restaurants')
    const destinationInfoBlocks = message.ui_blocks.filter(block => block.type === 'destination_info')

    const hasAny = activitiesBlocks.length > 0 || attractionsBlocks.length > 0 ||
                   restaurantsBlocks.length > 0 || destinationInfoBlocks.length > 0

    if (!hasAny) return null

    return (
      <div className="space-y-4 mt-4 w-full sm:max-w-[85%]">
        {/* Activities */}
        {activitiesBlocks.map((block, idx) => (
          <ListBlock
            key={`activities-${idx}`}
            title={block.title || 'Things to Do'}
            items={block.data || []}
            type="activities"
          />
        ))}

        {/* Attractions */}
        {attractionsBlocks.map((block, idx) => (
          <ListBlock
            key={`attractions-${idx}`}
            title={block.title || 'Must-See Attractions'}
            items={block.data || []}
            type="attractions"
          />
        ))}

        {/* Restaurants */}
        {restaurantsBlocks.map((block, idx) => (
          <ListBlock
            key={`restaurants-${idx}`}
            title={block.title || 'Recommended Restaurants'}
            items={block.data || []}
            type="restaurants"
          />
        ))}

        {/* Destination Info */}
        {destinationInfoBlocks.map((block, idx) => (
          <DestinationInfo
            key={`destination-info-${idx}`}
            data={block.data || {}}
          />
        ))}
      </div>
    )
  }

  return (
    <div
      id={`message-${message.id}`}
      className={`w-full py-4 sm:py-6 px-3 sm:px-4 message-slide-in`}
      style={{
        background: isUser ? 'var(--gpt-background)' : 'var(--gpt-background)'
      }}
    >
      <div id="message-container" className="mx-auto flex gap-2 sm:gap-4 items-start flex-row overflow-visible" style={{ maxWidth: '780px' }}>
        {/* Avatar - Only show for assistant */}
        {!isUser && (
          <div className="flex-shrink-0">
            <div
              className="w-7 h-7 sm:w-9 sm:h-9 rounded-full flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                boxShadow: 'var(--gpt-shadow-sm)'
              }}
            >
              <Bot size={16} className="sm:w-[18px] sm:h-[18px]" style={{ color: 'white' }} />
            </div>
          </div>
        )}

        {/* Message Content */}
        <div className={`flex-1 min-w-0 ${isUser ? 'flex flex-col items-end' : 'text-left'}`}>
          {isUser ? (
            message.isSuggestionClick ? (
              // Suggestion click: show as subtle label instead of full message bubble
              <div className="w-full flex justify-end">
                <div
                  className="text-xs sm:text-sm py-1 px-2 rounded"
                  style={{
                    color: 'var(--gpt-text-muted)',
                    background: 'var(--gpt-hover)',
                  }}
                >
                  <span style={{ opacity: 0.7 }}>{SUGGESTION_CLICK_PREFIX}</span>{' '}
                  <span style={{ fontWeight: 500 }}>
                    {message.content.startsWith(SUGGESTION_CLICK_PREFIX)
                      ? message.content.slice(SUGGESTION_CLICK_PREFIX.length).trim()
                      : message.content}
                  </span>
                </div>
              </div>
            ) : (
              // Regular user message: full bubble
              <>
                <div className="relative group flex items-start justify-end max-w-full gap-1.5 sm:gap-2">
                  <div
                    className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-2xl"
                    style={{
                      background: '#5b7cf6',
                      color: 'white',
                      boxShadow: 'var(--gpt-shadow-sm)',
                      maxWidth: '85%',
                      wordBreak: 'break-word'
                    }}
                  >
                    <p className="whitespace-pre-wrap text-sm sm:text-base">
                      {message.content}
                    </p>
                  </div>
                  {/* User Avatar */}
                  <div className="flex-shrink-0">
                    <div
                      className="w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center"
                      style={{
                        background: '#10b981',
                        boxShadow: 'var(--gpt-shadow-sm)'
                      }}
                    >
                      <User size={14} className="sm:w-4 sm:h-4" style={{ color: 'white' }} />
                    </div>
                  </div>
                </div>
                {/* Timestamp for user message */}
                <div
                  className="message-timestamp text-right mt-1 mr-8 sm:mr-10"
                  title={formatFullTimestamp(message.timestamp)}
                >
                  {relativeTime}
                </div>
              </>
            )
          ) : (
            <div className="w-full">
              {/* 1. Render provider-specific carousels (eBay, Amazon, etc.) */}
              {renderProviderCarousels()}

              {/* 2. Render new format products (Our Recommendations) */}
              {renderNewFormatProducts()}

              {/* 3. Render old carousels */}
              {renderCarousels()}

              {/* 4. Render text content (intro before comparison) */}
              {message.content && (
                <div className="w-full sm:max-w-[85%]">
                  <div
                    className="px-3 sm:px-5 py-3 sm:py-4 rounded-2xl"
                    style={{
                      background: 'var(--gpt-assistant-message)',
                      border: '1px solid rgba(0,0,0,0.05)',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                    }}
                  >
                    <div className="prose prose-sm sm:prose-base max-w-none [&>*:first-child]:mt-0 [&>h2]:text-lg [&>h2]:sm:text-xl [&>h2]:font-bold [&>h2]:mt-4 [&>h2]:mb-3" style={{ color: 'var(--gpt-text)' }}>
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                    {/* Model attribution - Hidden */}
                    <div className="flex items-center justify-end gap-1.5 mt-3 pt-2.5 border-t" style={{ borderColor: 'rgba(0,0,0,0.06)', display: 'none' }}>
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ opacity: 0.4 }}>
                        <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1"/>
                        <circle cx="6" cy="6" r="2" fill="currentColor"/>
                      </svg>
                      <span className="text-xs italic" style={{ color: 'var(--gpt-text-muted)', opacity: 0.8 }}>
                        Answered by OpenAI — gpt-4o-mini
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* 5. Render product comparison table (after intro text) */}
              {renderComparisonTable()}

              {/* 6. Render travel UI blocks (hotels + flights side by side on desktop) */}
              {renderTravelCards()}
              {renderItinerary()}
              {renderDestinationFacts()}

              {/* 4. Render follow-up questions (for travel flow) */}
              {message.followups && (
                <div className={`w-full sm:max-w-[85%] ${message.content || message.itinerary || message.ui_blocks?.some(block =>
                  ['hotel_cards', 'flight_cards', 'hotels', 'flights'].includes(block.block_type || block.type)
                ) ? "mt-4" : ""}`}>
                  <div
                    className="px-3 sm:px-5 py-3 sm:py-4 rounded-2xl"
                    style={{
                      background: 'var(--gpt-assistant-message)',
                      border: '1px solid rgba(0,0,0,0.05)',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                    }}
                  >
                    {/* Handle structured followups format */}
                    {typeof message.followups === 'object' && !Array.isArray(message.followups) ? (
                      <>
                        {/* Intro */}
                        {message.followups.intro && (
                          <p className="text-sm sm:text-base font-medium mb-3" style={{ color: 'var(--gpt-text)' }}>
                            {message.followups.intro}
                          </p>
                        )}
                        {/* Questions list */}
                        {message.followups.questions && message.followups.questions.length > 0 && (
                          <ul className="space-y-2 mb-3">
                            {message.followups.questions.map((q: { slot: string; question: string }, idx: number) => (
                              <li key={idx} className="flex items-start gap-2 text-sm sm:text-base" style={{ color: 'var(--gpt-text)' }}>
                                <span className="text-blue-500 font-bold">•</span>
                                <span>{q.question}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                        {/* Closing */}
                        {message.followups.closing && (
                          <p className="text-sm sm:text-base italic" style={{ color: 'var(--gpt-text-muted)' }}>
                            {message.followups.closing}
                          </p>
                        )}
                      </>
                    ) : Array.isArray(message.followups) && message.followups.length > 0 ? (
                      /* Handle legacy array format */
                      message.followups.map((question, idx) => (
                        <p key={idx} className="text-sm sm:text-base mb-2 last:mb-0" style={{ color: 'var(--gpt-text)' }}>{question}</p>
                      ))
                    ) : null}
                  </div>
                </div>
              )}

              {/* 5. Render product recommendations article (new format) */}
              {renderProductRecommendations()}

              {/* 6. Render affiliate links grouped by product (new format) */}
              {renderAffiliateLinks()}

              {/* 7. Render product reviews (old format - for backward compatibility) */}
              {renderProductReviews()}

              {/* 8. Render product cards (old format - for backward compatibility) */}
              {renderProductCards()}

              {/* 9. Render next step suggestions (clickable follow-up questions) */}
              {message.next_suggestions && message.next_suggestions.length > 0 && (
                <div className="mt-4 w-full sm:max-w-[85%]">
                  <div className="flex flex-wrap gap-2">
                    {message.next_suggestions.map((suggestion: NextSuggestion, idx: number) => (
                      <button
                        key={suggestion.id || idx}
                        className="px-3 sm:px-4 py-2 rounded-full text-xs sm:text-sm transition-all"
                        style={{
                          background: 'var(--gpt-accent-light)',
                          border: '1px solid var(--gpt-accent)',
                          color: 'var(--gpt-accent)',
                          cursor: 'pointer',
                          fontWeight: 500,
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'var(--gpt-accent)'
                          e.currentTarget.style.color = '#ffffff'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'var(--gpt-accent-light)'
                          e.currentTarget.style.color = 'var(--gpt-accent)'
                        }}
                        onClick={() => {
                          // Dispatch custom event to send this as a new message
                          const event = new CustomEvent('sendSuggestion', {
                            detail: { question: suggestion.question }
                          })
                          window.dispatchEvent(event)
                        }}
                      >
                        {suggestion.question}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Timestamp for assistant message */}
              <div
                className="message-timestamp mt-2"
                title={formatFullTimestamp(message.timestamp)}
              >
                {relativeTime}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
