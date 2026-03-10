import Link from 'next/link'

export const metadata = {
  title: 'Privacy Policy — ReviewGuide.ai',
  description: 'Privacy policy for ReviewGuide.ai',
}

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
      <Link
        href="/browse"
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--text)] transition-colors mb-8"
      >
        &larr; Back to Browse
      </Link>

      <h1 className="font-serif text-3xl sm:text-4xl font-semibold text-[var(--text)] tracking-tight mb-2">
        Privacy Policy
      </h1>
      <p className="text-sm text-[var(--text-muted)] mb-10">
        Effective Date: March 10, 2026
      </p>

      <div className="prose-editorial space-y-8">
        <p className="text-[var(--text-secondary)] leading-relaxed">
          ReviewGuide.ai (&ldquo;we,&rdquo; &ldquo;our,&rdquo; or &ldquo;us&rdquo;) respects your
          privacy and is committed to protecting your personal information.
        </p>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Information We Collect
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed mb-2">We may collect:</p>
          <ul className="list-disc pl-5 space-y-1 text-[var(--text-secondary)] leading-relaxed">
            <li>Basic usage data such as IP address, browser type, and device information</li>
            <li>Pages viewed and interactions on the site</li>
            <li>Information voluntarily provided through forms or email contact</li>
          </ul>
          <p className="text-[var(--text-secondary)] leading-relaxed mt-2">
            We do not require users to create accounts to access product research features.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            How We Use Information
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed mb-2">
            We use collected information to:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-[var(--text-secondary)] leading-relaxed">
            <li>Improve site performance and user experience</li>
            <li>Analyze traffic and usage trends</li>
            <li>Prevent fraud or misuse</li>
            <li>Comply with legal obligations</li>
          </ul>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Cookies and Tracking
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            We use cookies and similar technologies for analytics and affiliate tracking.
            Third-party affiliate partners, including Amazon and other networks, may use
            cookies to track purchases made through our referral links. You can disable
            cookies in your browser settings at any time.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Third-Party Links
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            Our website contains affiliate links to third-party websites. We are not
            responsible for the privacy practices or content of those external sites.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Data Security
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            We take reasonable technical and organizational measures to protect user data.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Changes
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            We may update this policy periodically. Continued use of the site constitutes
            acceptance of any updates.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Contact
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            Questions about this policy? Reach us at{' '}
            <a
              href="mailto:mike@reviewguide.ai"
              className="text-[var(--primary)] hover:underline"
            >
              mike@reviewguide.ai
            </a>
          </p>
        </section>

        <div className="border-t border-[var(--border)] pt-8">
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            AI Content Disclosure
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed mb-3">
            ReviewGuide.ai uses artificial intelligence technology to generate product
            summaries, comparisons, and research insights. Our content is designed to
            provide informational guidance based on aggregated data and structured analysis.
          </p>
          <p className="text-[var(--text-secondary)] leading-relaxed mb-3">
            While we strive for accuracy and usefulness, information may not always reflect
            the most current product updates or individual user experiences. Users should
            independently verify product details, specifications, and pricing directly with
            retailers before making purchasing decisions.
          </p>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            ReviewGuide.ai does not claim to represent official reviews from any specific
            retailer unless explicitly stated.
          </p>
        </div>
      </div>
    </div>
  )
}
