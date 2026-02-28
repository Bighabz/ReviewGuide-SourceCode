export interface CuratedTopic {
  title: string
  links: string[]
}

export type CuratedCategory = Record<string, CuratedTopic[]>

export const curatedLinks: CuratedCategory = {
  electronics: [
    {
      title: 'Best Noise-Cancelling Headphones',
      links: [
        'https://amzn.to/4cg2c2g',
        'https://amzn.to/46sYSNy',
        'https://amzn.to/40hVQbz',
        'https://amzn.to/4qWWrtW',
        'https://amzn.to/4kZCHVl',
      ],
    },
    {
      title: 'Top Laptops for Students in 2026',
      links: [
        'https://amzn.to/4tSpXE1',
        'https://amzn.to/3OtNdIf',
        'https://amzn.to/40srrqS',
        'https://amzn.to/3ZTVpE2',
        'https://amzn.to/4kUxiPj',
      ],
    },
    {
      title: 'Best Budget Smartphones Under $400',
      links: [
        'https://amzn.to/40wHa8k',
        'https://amzn.to/4baYypf',
        'https://amzn.to/4s7D16v',
        'https://amzn.to/4ucdsmS',
        'https://amzn.to/4aAkUjS',
      ],
    },
    {
      title: 'Best Bluetooth Speakers',
      links: [
        'https://amzn.to/40tnceG',
        'https://amzn.to/4cW8fcm',
        'https://amzn.to/3OE2Rkf',
        'https://amzn.to/4aUTEeI',
        'https://amzn.to/46ZowJS',
        'https://amzn.to/4sflr0x',
      ],
    },
  ],
  'home-appliances': [
    {
      title: 'Best Robot Vacuums for Pet Hair',
      links: [
        'https://amzn.to/4kZU08C',
        'https://amzn.to/3ZYKrNt',
        'https://amzn.to/4cK6Jdq',
        'https://amzn.to/4sxhxAv',
        'https://amzn.to/46qmUst',
      ],
    },
    {
      title: 'Best Compact Washing Machines',
      links: [
        'https://amzn.to/4u2A4Gq',
        'https://amzn.to/4kXfNxK',
        'https://amzn.to/4qRmimV',
        'https://amzn.to/4siBCKJ',
        'https://amzn.to/4sel4Dv',
      ],
    },
    {
      title: 'Dyson vs Shark: Which Vacuum Wins?',
      links: [
        'https://amzn.to/4r3yGk3',
        'https://amzn.to/4s43SQQ',
        'https://amzn.to/4aC3lQt',
        'https://amzn.to/46te6SN',
        'https://amzn.to/4kZFii3',
      ],
    },
    {
      title: 'Best Espresso Machines Under $500',
      links: [
        'https://amzn.to/46NZBZZ',
        'https://amzn.to/4bgoDlV',
        'https://amzn.to/4kVjGTL',
        'https://amzn.to/4rxiqbW',
        'https://amzn.to/4b8KI6O',
      ],
    },
  ],
  'health-wellness': [
    {
      title: 'Best Standing Desks for Back Pain',
      links: [
        'https://amzn.to/4rHjBWv',
        'https://amzn.to/3ZTY3ts',
        'https://amzn.to/3MTqx3r',
        'https://amzn.to/3ZYlH84',
        'https://amzn.to/3MIFHsr',
      ],
    },
    {
      title: 'Best Supplements for Energy and Focus',
      links: [
        'https://amzn.to/4aSaSto',
        'https://amzn.to/4u2BIrA',
        'https://amzn.to/3ZTq1FL',
        'https://amzn.to/4cgr1el',
        'https://amzn.to/4kXo0lz',
      ],
    },
    {
      title: 'Theragun vs Hypervolt: Which Massage Gun Is Better?',
      links: [
        'https://amzn.to/4kZ7fX1',
        'https://amzn.to/4l2yxMq',
        'https://amzn.to/4tXXqNg',
        'https://amzn.to/4qWfnsA',
        'https://amzn.to/4l0t7kX',
      ],
    },
    {
      title: 'Best Fitness Trackers Under $100',
      links: [
        'https://amzn.to/3ZXGdpy',
        'https://amzn.to/4aRMcBb',
        'https://amzn.to/4scnhiz',
        'https://amzn.to/4tWNnb3',
        'https://amzn.to/46u0M0j',
      ],
    },
    {
      title: 'Top-Rated Supplements for Weight Loss',
      links: [
        'https://amzn.to/4baXYIa',
        'https://amzn.to/46OSVuD',
        'https://amzn.to/3OM6Yuw',
        'https://amzn.to/4s88HZr',
        'https://amzn.to/3OBZXg0',
        'https://amzn.to/4cPmL5G',
      ],
    },
    {
      title: 'Best Supplements for Menopause Support',
      links: [
        'https://amzn.to/4sdlxpu',
        'https://amzn.to/46P16aj',
        'https://amzn.to/46uZPVx',
        'https://amzn.to/4qY1JVW',
      ],
    },
  ],
  'outdoor-fitness': [
    {
      title: 'Best Hiking Boots for Beginners',
      links: [
        'https://amzn.to/4aIxo7G',
        'https://amzn.to/4aU6jP2',
        'https://amzn.to/3MvKUUr',
        'https://amzn.to/3OAEGDf',
        'https://amzn.to/3P2NBNS',
      ],
    },
    {
      title: 'Best Shoes for Flat Feet',
      links: [
        'https://amzn.to/3P4MahS',
        'https://amzn.to/3MvLcdZ',
        'https://amzn.to/4si597f',
        'https://amzn.to/47ebcRY',
        'https://amzn.to/3ZYOMQL',
      ],
    },
    {
      title: 'Garmin vs Apple Watch for Fitness',
      links: [
        'https://amzn.to/46rIc94',
        'https://amzn.to/4tXZNQ5',
        'https://amzn.to/4rFsj7D',
        'https://amzn.to/4l6ws1R',
        'https://amzn.to/4tWPfAB',
      ],
    },
    {
      title: 'Best Home Treadmills Under $1,000',
      links: [
        'https://amzn.to/4aC70hb',
        'https://amzn.to/4siFxXX',
        'https://amzn.to/46pe8uP',
        'https://amzn.to/46VPrGw',
        'https://amzn.to/4qX2ZJ2',
      ],
    },
  ],
  'fashion-style': [
    {
      title: 'Best White Sneakers for Everyday Wear',
      links: [
        'https://amzn.to/3ZXKuJu',
        'https://amzn.to/476uRmL',
        'https://amzn.to/4cguOZg',
        'https://amzn.to/4rE2h4J',
        'https://amzn.to/4qX1Hh0',
      ],
    },
    {
      title: "Best Affordable Jewelry That Won't Tarnish",
      links: [
        'https://amzn.to/3MKtN1c',
        'https://amzn.to/4rHcIo2',
        'https://amzn.to/46vziY9',
        'https://amzn.to/4l6BoUr',
        'https://amzn.to/4aXQ2Jb',
      ],
    },
    {
      title: 'Best Streetwear Brands in 2026',
      links: [
        'https://amzn.to/3OyKi0U',
        'https://amzn.to/3ZYtGly',
        'https://amzn.to/40wRNYM',
        'https://amzn.to/4shzrHk',
        'https://amzn.to/4sezXWl',
      ],
    },
    {
      title: 'Best Watches Under $500',
      links: [
        'https://amzn.to/4aN66gE',
        'https://amzn.to/3N5VIsv',
        'https://amzn.to/4qX2XAK',
        'https://amzn.to/4aXQTJN',
        'https://amzn.to/4qU4Tdh',
      ],
    },
  ],
  'smart-home': [
    {
      title: 'Best Alexa-Compatible Smart Home Gadgets',
      links: [
        'https://amzn.to/4l2GelM',
        'https://amzn.to/4r3IWsz',
        'https://amzn.to/3OPqRRr',
        'https://amzn.to/46Y9EeO',
        'https://amzn.to/4sg5N5d',
        'https://amzn.to/4qTKyov',
        'https://amzn.to/3P2VD9u',
      ],
    },
  ],
  'kids-toys': [
    {
      title: 'Hottest Toys of 2026',
      links: [
        'https://amzn.to/4u2gfis',
        'https://amzn.to/4qX4iHM',
        'https://amzn.to/4rzKtHH',
        'https://amzn.to/3ZXSWZk',
        'https://amzn.to/4cgFw1Y',
        'https://amzn.to/4r3JVcf',
        'https://amzn.to/4sdnEd0',
        'https://amzn.to/3MwI5CB',
      ],
    },
  ],
  baby: [
    {
      title: 'Baby Essentials Every New Parent Needs',
      links: [
        'https://amzn.to/40y4ZfW',
        'https://amzn.to/46pFVLM',
        'https://amzn.to/4kTSBjM',
        'https://amzn.to/4kU8p68',
        'https://amzn.to/4cOOKT6',
        'https://amzn.to/4l08rtk',
        'https://amzn.to/4qTLWHL',
      ],
    },
  ],
  'big-tall': [
    {
      title: 'Best Big & Tall Clothing for Men',
      links: [
        'https://amzn.to/4cbMKnN',
        'https://amzn.to/3MwIkO1',
        'https://amzn.to/401kjl9',
        'https://amzn.to/4bcefMY',
        'https://amzn.to/4seDT9z',
        'https://amzn.to/4aEwmLq',
      ],
    },
  ],
}
