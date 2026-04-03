import { redirect } from 'next/navigation'

/**
 * /browse intentionally redirects to the homepage.
 * The homepage (/) serves as the primary browse/discover experience
 * with category navigation, content rows, and search.
 * This redirect exists to handle legacy links and user expectations.
 * QAR-19: converts a "silent unexplained redirect" to a "documented intentional redirect."
 */
export default function BrowsePage() {
  redirect('/')
}
