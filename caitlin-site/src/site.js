// Every practice-specific detail lives here so the whole site can be
// re-pointed at the real practice by editing one file.
// Everything below is PLACEHOLDER content for the prototype.

module.exports = {
  practice: {
    name: 'Matilija Family Medicine',
    shortName: 'Matilija',
    tagline: 'Integrative family medicine in Ojai',
    descriptor: 'A small, personal family practice for every age, right here in the Ojai Valley.',
    url: 'https://matilijafamilymedicine.com',
    opening: 'Now welcoming new patients and families for fall 2026',
  },
  doctor: {
    first: 'Caitlin',
    last: 'Hartwell',            // placeholder surname
    credentials: 'DO',
    display: 'Dr. Caitlin Hartwell, DO',
    short: 'Dr. Caitlin',
    title: 'Board-certified family physician',
    photo: '/img/dr-caitlin.webp',
    education: [
      { label: 'Medical school', value: 'Touro College of Osteopathic Medicine' },
      { label: 'Residency', value: 'University of Wisconsin, Department of Family Medicine and Community Health' },
      { label: 'Certifications', value: 'Advanced Cardiac Life Support (ACLS), Pediatric Advanced Life Support (PALS), Advanced Life Support in Obstetrics (ALSO)' },
    ],
  },
  contact: {
    phone: '(805) 555-0142',
    phoneHref: 'tel:+18055550142',
    email: 'hello@matilijafamilymedicine.com',
    address1: '312 East Matilija Street, Suite B',
    address2: 'Ojai, CA 93023',
    mapQuery: 'Matilija Street, Ojai, CA 93023',
    hours: [
      { day: 'Monday to Friday', time: '8:00 am to 5:00 pm' },
      { day: 'Same-day visits', time: 'Held open every weekday' },
      { day: 'After-hours line', time: 'Members: evenings and weekends' },
    ],
    serviceArea: 'Home visits available throughout Ojai, Meiners Oaks, Mira Monte, Oak View and the upper valley.',
    portalUrl: '#patient-portal',      // placeholder: EHR patient portal link
    joinUrl: '/schedule?type=meet',    // placeholder: membership signup
    instagram: '#', facebook: '#',
  },
  insurance: [
    'Anthem Blue Cross', 'Blue Shield of California', 'Aetna', 'Cigna',
    'UnitedHealthcare', 'Medicare',
  ],
  membership: {
    intro: 'Your insurance covers your visits the way it always has. A modest annual membership covers everything insurance was never designed to pay for: unhurried time, same-day access, and a doctor who can come to you.',
    tiers: [
      {
        name: 'Individual',
        price: '$1,800',
        per: 'per year',
        alt: 'or $160 a month',
        who: 'One adult',
        note: 'Adults 18 and over',
      },
      {
        name: 'Family',
        price: '$3,600',
        per: 'per year',
        alt: 'or $320 a month',
        who: 'Two adults and all children at home',
        note: 'Most popular',
        featured: true,
      },
      {
        name: 'Child',
        price: '$600',
        per: 'per year',
        alt: 'or $55 a month',
        who: 'Each child, when a parent is a member',
        note: 'Newborns through age 17',
      },
    ],
    seniors: 'Adults 65 and older on Medicare: $1,500 per year.',
    includes: [
      'Same-day or next-day appointments, always',
      'Unhurried visits of 45 to 60 minutes',
      'Direct phone and text line to Dr. Caitlin',
      'After-hours and weekend access for urgent needs',
      'Two home visits per year included; additional visits at a flat rate',
      'An annual comprehensive wellness assessment and personalized plan',
      'Integrative care: nutrition, sleep, stress, movement and botanicals',
      'Osteopathic manipulative treatment when it helps',
      'Coordination with specialists, labs, imaging and pharmacies',
      'Care for the whole family under one roof',
    ],
    fine: [
      'Membership is billed annually or monthly and can be cancelled with 30 days notice.',
      'Office visits, labs, procedures and vaccines are billed to your insurance as usual. Copays and deductibles still apply.',
      'Uninsured patients are welcome. Ask us about transparent self-pay visit pricing.',
      'A limited number of sliding-scale memberships are set aside for valley families each year.',
    ],
  },
  services: [
    {
      slug: 'whole-family', icon: 'spot_family',
      name: 'Primary care for the whole family',
      blurb: 'Newborns, grandparents and everyone in between, all seen by the same doctor who knows your story.',
      detail: 'Well visits, sick visits, physicals, vaccines, screenings and the everyday questions that come up in between. One doctor for the whole household means nothing gets lost between offices.',
    },
    {
      slug: 'same-day', icon: 'spot_clock',
      name: 'Same-day access',
      blurb: 'Call in the morning, be seen that day. Time is held open every weekday for whatever comes up.',
      detail: 'Members reach Dr. Caitlin directly by phone or text. Most concerns are handled the same day, in the office, at home, or by video, without a trip to urgent care.',
    },
    {
      slug: 'home-visits', icon: 'spot_house',
      name: 'Home and after-hours visits',
      blurb: 'For newborns, elders, anyone too sick to travel, or simply when home is the better place to be seen.',
      detail: 'House calls throughout the Ojai Valley, plus an after-hours line for evenings and weekends. A doctor at your kitchen table is still one of the best tools in medicine.',
    },
    {
      slug: 'integrative', icon: 'spot_bowl',
      name: 'Integrative and lifestyle medicine',
      blurb: 'Evidence-based conventional care, thoughtfully combined with nutrition, sleep, movement, stress care and botanicals.',
      detail: 'Integrative does not mean instead of. It means looking at the whole picture, choosing the gentlest effective option first, and being honest about what the evidence shows.',
    },
    {
      slug: 'pediatrics', icon: 'spot_child',
      name: 'Pediatrics and well-child care',
      blurb: 'Unhurried well-child visits, developmental check-ins, school forms and same-day care when they wake up sick.',
      detail: 'From the first weeks at home through the teenage years. Parents get a direct line for the questions that never seem to happen during office hours.',
    },
    {
      slug: 'chronic', icon: 'spot_heart',
      name: 'Chronic condition care',
      blurb: 'Blood pressure, diabetes, thyroid, asthma, anxiety, and the long-haul conditions that deserve real time.',
      detail: 'Longer visits mean we can actually talk about what is working, adjust the plan together, and coordinate with any specialists involved.',
    },
    {
      slug: 'womens-health', icon: 'spot_teapot',
      name: "Women's health",
      blurb: 'Annual exams, contraception, perimenopause and menopause, and support through every season.',
      detail: 'Care that takes hormones, sleep, mood and life stage seriously, with time to talk it through.',
    },
    {
      slug: 'omt', icon: 'spot_stethoscope',
      name: 'Osteopathic manipulative treatment',
      blurb: 'Hands-on treatment for back and neck pain, headaches, and musculoskeletal problems, offered as part of your visit.',
      detail: 'As an osteopathic physician, Dr. Caitlin is trained in OMT, a gentle hands-on approach that can ease pain and improve mobility alongside conventional treatment.',
    },
    {
      slug: 'wellness-plan', icon: 'spot_book',
      name: 'Annual comprehensive assessment',
      blurb: 'A yearly deep dive into your health history, labs, goals and habits, turned into a plan you actually want to follow.',
      detail: 'Every member gets an extended annual visit and a written, personalized plan that we revisit together through the year.',
    },
  ],
  faq: [
    {
      q: 'What does "integrative family medicine" mean?',
      a: 'It means conventional, evidence-based family medicine practiced by a board-certified physician, combined with real attention to nutrition, sleep, movement, stress and, where the evidence supports it, botanicals and hands-on osteopathic care. We use the whole toolbox and are honest about what each tool can do.',
    },
    {
      q: 'Do you take my insurance?',
      a: 'We are in network with most major plans, including Anthem Blue Cross, Blue Shield of California, Aetna, Cigna, UnitedHealthcare and Medicare. Visits, labs and procedures are billed to insurance as usual. The annual membership is separate and is not billed to insurance.',
    },
    {
      q: 'Why is there a membership fee on top of insurance?',
      a: 'Insurance pays for short visits and not much else. The membership is what lets the practice stay small, hold time open every day, answer the phone, and come to your home. It replaces the volume model with a relationship model.',
    },
    {
      q: 'Can I use my HSA or FSA for the membership?',
      a: 'Often, yes. Many members pay the fee with HSA or FSA funds. Check with your plan administrator, and we are happy to provide an itemized receipt.',
    },
    {
      q: 'What counts as "same-day"?',
      a: 'If you reach out before mid-afternoon on a weekday, you will be offered a visit that day, in the office, at home or by video. Later in the day, and on weekends, urgent concerns are handled by phone and seen first thing the next morning if needed.',
    },
    {
      q: 'How do home visits work?',
      a: 'Two home visits a year are included in every membership, and additional visits are available at a flat rate. We serve Ojai, Meiners Oaks, Mira Monte, Oak View and the upper valley. Home visits are wonderful for newborns, elders, post-surgical checks and anyone who is too unwell to travel.',
    },
    {
      q: 'What if I need a specialist or a hospital?',
      a: 'Dr. Caitlin coordinates referrals, shares records, and stays involved. When you are admitted to a hospital, she stays in contact with the team caring for you and sees you in the office soon after discharge.',
    },
    {
      q: 'Can I try it before I commit?',
      a: 'Yes. Book a complimentary 20-minute meet-and-greet, in person or by video, to see if the practice is a fit.',
    },
    {
      q: 'What if I do not have insurance?',
      a: 'You are welcome here. Members without insurance pay a transparent flat rate per visit, and we work with local labs and pharmacies to keep costs predictable.',
    },
  ],
  visitTypes: [
    { value: 'meet', label: 'Free 20-minute meet and greet' },
    { value: 'new', label: 'New patient visit' },
    { value: 'sameday', label: 'Same-day sick visit' },
    { value: 'annual', label: 'Annual comprehensive assessment' },
    { value: 'followup', label: 'Follow-up visit' },
    { value: 'home', label: 'Home visit' },
    { value: 'video', label: 'Video visit' },
  ],
};
