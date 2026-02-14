'use client'

import { User, Copy, Check, ArrowRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'
import DOMPurify from 'dompurify'
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
import CarRentalCard from './CarRentalCard'
import ReviewSources from './ReviewSources'
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
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(message.content)
      } else {
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

  // Render review sources block (from SerpAPI review search)
  const renderReviewSources = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    const reviewBlocks = message.ui_blocks.filter(block => block.type === 'review_sources')
    if (reviewBlocks.length === 0) return null

    return (
      <div className="space-y-6 mb-6">
        {reviewBlocks.map((block, idx) => (
          <ReviewSources key={idx} data={block.data || { products: [] }} title={block.title} />
        ))}
      </div>
    )
  }

  // Separate carousel and product cards rendering
  const renderCarousels = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) {
      return null
    }

    const carousels = message.ui_blocks.filter(block => block.block_type === 'carousel')
    if (carousels.length === 0) return null

    return (
      <div className="space-y-6 mb-6">
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
      <div className="space-y-6 mb-6">
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
            source: product.source,
            description: product.description
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
      <div className="space-y-6 mb-6">
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
      <div className="space-y-6 mt-6 w-full">
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
      <div className="space-y-6 mt-6 w-full">
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
      <div className="space-y-6 mt-6 w-full">
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
      <div className="space-y-4 mt-6 w-full">
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
      <div className="space-y-6 mt-6 w-full">
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
      <div className="space-y-6 mt-6 w-full">
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
        <div className="mt-6 w-full">
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
      <div className="mt-6 w-full">
        {hasHotels && hotelBlocks.map((block, idx) => (
          <HotelCards key={`hotel-${idx}`} hotels={block.payload?.hotels || block.data || []} />
        ))}
        {hasFlights && flightBlocks.map((block, idx) => (
          <FlightCards key={`flight-${idx}`} flights={block.payload?.flights || block.data || []} />
        ))}
      </div>
    )
  }

  const renderCarRentals = () => {
    if (!message.ui_blocks || message.ui_blocks.length === 0) return null

    const carBlocks = message.ui_blocks.filter(block => block.type === 'cars')
    if (carBlocks.length === 0) return null

    return (
      <div className="space-y-6 mt-6 w-full">
        {carBlocks.map((block, idx) => (
          <CarRentalCard key={idx} cars={block.data || []} />
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
          <div className="space-y-6 mt-6 w-full">
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
        <div className="space-y-6 mt-6 w-full">
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
      <div className="space-y-6 mb-6 w-full">
        {comparisonBlocks.map((block, idx) => {
          // New format: comparison_html with HTML content
          if (block.type === 'comparison_html' && block.data?.html) {
            // SECURITY: Sanitize HTML to prevent XSS attacks
            const sanitizedHtml = DOMPurify.sanitize(block.data.html, {
              ADD_TAGS: ['style'],  // Allow style tags for table formatting
              ADD_ATTR: ['target', 'rel'],  // Allow link attributes
            })
            return (
              <div
                key={idx}
                className="comparison-html-container rounded-xl overflow-hidden shadow-card border border-[var(--border)]"
                style={{
                  background: 'var(--surface)',
                }}
                dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
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
      <div className="space-y-6 mt-6 w-full">
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
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      id={`message-${message.id}`}
      className="w-full py-4 sm:py-5 px-3 sm:px-4"
    >
      <div id="message-container" className="mx-auto flex gap-3 sm:gap-4 items-start flex-row overflow-visible" style={{ maxWidth: '780px' }}>
        {/* Avatar - Only show for assistant */}
        {!isUser && (
          <div className="flex-shrink-0 mt-0.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-[var(--primary)] shadow-sm">
              <img
                src="/images/ezgif-7b66ba24abcfdab0.gif"
                alt="AI"
                className="w-4 h-4 rounded"
              />
            </div>
          </div>
        )}

        {/* Message Content */}
        <div className={`flex-1 min-w-0 ${isUser ? 'flex flex-col items-end' : 'text-left'}`}>
          {isUser ? (
            message.isSuggestionClick ? (
              // Suggestion click: show as subtle pill
              <div className="w-full flex justify-end">
                <div className="text-xs sm:text-sm py-2 px-4 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)]">
                  <span className="opacity-60">{SUGGESTION_CLICK_PREFIX}</span>{' '}
                  <span className="font-medium text-[var(--text)]">
                    {message.content.startsWith(SUGGESTION_CLICK_PREFIX)
                      ? message.content.slice(SUGGESTION_CLICK_PREFIX.length).trim()
                      : message.content}
                  </span>
                </div>
              </div>
            ) : (
              // Regular user message: editorial bubble
              <>
                <div className="relative group flex items-start justify-end max-w-full gap-2.5">
                  <div className="px-4 py-3 rounded-2xl rounded-tr-md bg-[var(--primary)] text-white shadow-card">
                    <p className="whitespace-pre-wrap text-[15px] leading-relaxed">
                      {message.content}
                    </p>
                  </div>

                  {/* User Avatar */}
                  <div className="flex-shrink-0 mt-0.5">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center bg-[var(--surface-hover)] text-[var(--text-muted)] border border-[var(--border)]">
                      <User size={14} strokeWidth={1.5} />
                    </div>
                  </div>
                </div>
                {/* Timestamp */}
                <div className="text-[10px] text-[var(--text-muted)] text-right mt-1.5 mr-10">
                  {relativeTime}
                </div>
              </>
            )
          ) : (
            <div className="w-full">
              {/* Status indicator — shown while tools are working */}
              {!message.content && message.isThinking && (
                <div className="flex items-center gap-2 py-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] animate-pulse" />
                  <span className="text-sm text-[var(--text-secondary)] font-medium tracking-tight">
                    {message.statusText || 'Thinking...'}
                  </span>
                </div>
              )}

              {/* 1. Render text content FIRST (brief summary) */}
              {message.content && (
                <div className="w-full">
                  <div className="prose prose-sm sm:prose-base max-w-none
                      text-[var(--text)]
                      prose-headings:font-serif prose-headings:tracking-tight prose-headings:text-[var(--text)]
                      prose-p:text-[var(--text)] prose-p:leading-relaxed prose-p:text-[15px]
                      prose-strong:text-[var(--text)] prose-strong:font-semibold
                      prose-li:text-[var(--text)] prose-li:marker:text-[var(--text-muted)]
                      prose-pre:bg-[var(--surface)] prose-pre:border prose-pre:border-[var(--border)] prose-pre:rounded-xl
                      prose-a:text-[var(--primary)] prose-a:no-underline hover:prose-a:underline"
                  >
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                </div>
              )}

              {/* 2. Render review sources (from real review search) */}
              {renderReviewSources()}

              {/* 3. Render provider-specific carousels (eBay, Amazon, etc.) */}
              {renderProviderCarousels()}

              {/* 3. Render new format products (Our Recommendations) */}
              {renderNewFormatProducts()}

              {/* 4. Render old carousels */}
              {renderCarousels()}

              {/* 5. Render comparison table */}
              {renderComparisonTable()}

              {/* 6. Render travel UI blocks */}
              {renderTravelCards()}
              {renderCarRentals()}
              {renderItinerary()}
              {renderDestinationFacts()}

              {/* 7. Render product recommendations (article) */}
              {renderProductRecommendations()}

              {/* 8. Render affiliate links */}
              {renderAffiliateLinks()}

              {/* 9. Render legacy blocks */}
              {renderProductReviews()}
              {renderProductCards()}

              {/* 10. Render clarifier follow-up questions (structured slot-filling) */}
              {message.followups && typeof message.followups === 'object' && !Array.isArray(message.followups) && (
                <div className="w-full mt-5">
                  <div className="border border-[var(--border)] rounded-xl p-4 bg-[var(--surface)]">
                    {message.followups.intro && (
                      <p className="text-sm font-medium text-[var(--text)] mb-3">
                        {message.followups.intro}
                      </p>
                    )}
                    <div className="space-y-1.5">
                      {message.followups.questions && message.followups.questions.map((q: { slot: string; question: string }, idx: number) => (
                        <button
                          key={idx}
                          className="w-full text-left px-3.5 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--background)] hover:border-[var(--primary)] hover:bg-[var(--primary-light)] transition-all text-sm text-[var(--text)] flex items-center justify-between group"
                          onClick={() => {
                            const event = new CustomEvent('sendSuggestion', {
                              detail: { question: q.question }
                            })
                            window.dispatchEvent(event)
                          }}
                        >
                          <span>{q.question}</span>
                          <ArrowRight size={14} strokeWidth={1.5} className="opacity-0 group-hover:opacity-100 transition-opacity text-[var(--primary)]" />
                        </button>
                      ))}
                    </div>
                    {message.followups.closing && (
                      <p className="mt-3 text-xs italic text-[var(--text-muted)]">
                        {message.followups.closing}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* 11. Render conclusion text */}
              {message.ui_blocks?.filter((b: any) => b.type === 'conclusion').map((block: any, idx: number) => (
                <p key={`conclusion-${idx}`} className="text-sm text-[var(--text-muted)] mt-4 italic">
                  {block.data?.text}
                </p>
              ))}

              {/* Timestamp for assistant */}
              <div
                className="text-[10px] text-[var(--text-muted)] mt-2 ml-0.5"
                title={formatFullTimestamp(message.timestamp)}
              >
                {relativeTime}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
