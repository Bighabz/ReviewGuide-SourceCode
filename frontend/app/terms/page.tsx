import Link from 'next/link'

export const metadata = {
  title: 'Terms of Service — ReviewGuide.ai',
  description: 'Terms of service for ReviewGuide.ai',
}

export default function TermsPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
      <Link
        href="/browse"
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--text)] transition-colors mb-8"
      >
        &larr; Back to Browse
      </Link>

      <h1 className="font-serif text-3xl sm:text-4xl font-semibold text-[var(--text)] tracking-tight mb-2">
        Terms of Service
      </h1>
      <p className="text-sm text-[var(--text-muted)] mb-10">
        Effective Date: March 10, 2026
      </p>

      <div className="prose-editorial space-y-8">
        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Acceptance of Terms
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            By accessing or using ReviewGuide.ai, you agree to be bound by these Terms of
            Service. If you do not agree to these terms, please do not use the site.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Service Description
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            ReviewGuide.ai is an AI-powered product research and recommendation platform.
            We aggregate publicly available product data, reviews, and specifications to
            help users make more informed purchasing decisions.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            User Responsibilities
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed mb-2">
            When using ReviewGuide.ai, you agree not to:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-[var(--text-secondary)] leading-relaxed">
            <li>Use the service for any unlawful or prohibited purpose</li>
            <li>Scrape, crawl, or otherwise extract data from the site through automated means</li>
            <li>Attempt to gain unauthorized access to any part of the service</li>
            <li>Interfere with or disrupt the integrity or performance of the service</li>
            <li>Misrepresent your identity or affiliation when using the service</li>
          </ul>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            AI-Generated Content
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed mb-3">
            ReviewGuide.ai uses artificial intelligence to generate product summaries,
            comparisons, and research insights. This content is provided for informational
            purposes only and should not be considered professional, financial, or
            purchasing advice.
          </p>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            Users should independently verify product details, specifications, pricing,
            and availability directly with retailers before making any purchasing decisions.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Affiliate Links
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed mb-3">
            ReviewGuide.ai contains affiliate links to third-party retailer websites.
            When you click on these links and make a purchase, we may earn a commission
            at no additional cost to you.
          </p>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            As an Amazon Associate, we earn from qualifying purchases. Affiliate
            partnerships do not influence our analysis, opinions, or product evaluations.
            For more details, see our{' '}
            <Link
              href="/affiliate-disclosure"
              className="text-[var(--primary)] hover:underline"
            >
              Affiliate Disclosure
            </Link>
            .
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Intellectual Property
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            All content on ReviewGuide.ai, including text, graphics, logos, and software,
            is the property of ReviewGuide.ai or its content suppliers and is protected by
            intellectual property laws. You may not reproduce, distribute, or create
            derivative works from our content without prior written permission.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Disclaimers
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed mb-3">
            ReviewGuide.ai is provided &ldquo;as is&rdquo; and &ldquo;as available&rdquo;
            without warranties of any kind, either express or implied, including but not
            limited to implied warranties of merchantability, fitness for a particular
            purpose, or non-infringement.
          </p>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            We do not warrant that the information on our site is accurate, complete, or
            current. Product information, pricing, and availability are subject to change
            without notice.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Limitation of Liability
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            ReviewGuide.ai and its operators shall not be liable for any direct, indirect,
            incidental, consequential, or punitive damages arising from your use of the
            service, including but not limited to purchasing decisions made based on
            AI-generated content, product recommendations, or information provided on this site.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Changes to Terms
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            We reserve the right to update or modify these Terms of Service at any time.
            Changes will be effective immediately upon posting to this page. Your continued
            use of ReviewGuide.ai after any changes constitutes acceptance of the updated terms.
          </p>
        </section>

        <section>
          <h2 className="font-serif text-xl font-semibold text-[var(--text)] mb-3">
            Contact
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            Questions about these terms? Reach us at{' '}
            <a
              href="mailto:mike@reviewguide.ai"
              className="text-[var(--primary)] hover:underline"
            >
              mike@reviewguide.ai
            </a>
          </p>
        </section>
      </div>
    </div>
  )
}
