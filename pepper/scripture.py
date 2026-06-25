"""
The daily scripture.

A curated set of encouraging, public-domain verses (King James Version). The
"verse of the day" is chosen deterministically from the day of the year so it
rotates predictably and needs no network call. ``random_verse`` is exposed as a
tool so the owner can ask for one any time.
"""

import datetime

# Public-domain (KJV). Kept intentionally uplifting / steadying for a morning read.
VERSES = [
    ("Joshua 1:9", "Be strong and of a good courage; be not afraid, neither be thou dismayed: for the LORD thy God is with thee whithersoever thou goest."),
    ("Philippians 4:13", "I can do all things through Christ which strengtheneth me."),
    ("Proverbs 3:5-6", "Trust in the LORD with all thine heart; and lean not unto thine own understanding. In all thy ways acknowledge him, and he shall direct thy paths."),
    ("Isaiah 40:31", "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint."),
    ("Psalm 23:1", "The LORD is my shepherd; I shall not want."),
    ("Jeremiah 29:11", "For I know the thoughts that I think toward you, saith the LORD, thoughts of peace, and not of evil, to give you an expected end."),
    ("Romans 8:28", "And we know that all things work together for good to them that love God, to them who are the called according to his purpose."),
    ("Matthew 6:33", "But seek ye first the kingdom of God, and his righteousness; and all these things shall be added unto you."),
    ("Psalm 46:1", "God is our refuge and strength, a very present help in trouble."),
    ("2 Timothy 1:7", "For God hath not given us the spirit of fear; but of power, and of love, and of a sound mind."),
    ("Proverbs 16:3", "Commit thy works unto the LORD, and thy thoughts shall be established."),
    ("Philippians 4:6-7", "Be careful for nothing; but in every thing by prayer and supplication with thanksgiving let your requests be made known unto God. And the peace of God, which passeth all understanding, shall keep your hearts and minds through Christ Jesus."),
    ("Psalm 118:24", "This is the day which the LORD hath made; we will rejoice and be glad in it."),
    ("Isaiah 41:10", "Fear thou not; for I am with thee: be not dismayed; for I am thy God: I will strengthen thee; yea, I will help thee; yea, I will uphold thee with the right hand of my righteousness."),
    ("Galatians 6:9", "And let us not be weary in well doing: for in due season we shall reap, if we faint not."),
    ("Psalm 37:5", "Commit thy way unto the LORD; trust also in him; and he shall bring it to pass."),
    ("1 Corinthians 16:13", "Watch ye, stand fast in the faith, quit you like men, be strong."),
    ("Colossians 3:23", "And whatsoever ye do, do it heartily, as to the Lord, and not unto men."),
    ("Psalm 19:14", "Let the words of my mouth, and the meditation of my heart, be acceptable in thy sight, O LORD, my strength, and my redeemer."),
    ("Proverbs 21:5", "The thoughts of the diligent tend only to plenteousness; but of every one that is hasty only to want."),
    ("James 1:5", "If any of you lack wisdom, let him ask of God, that giveth to all men liberally, and upbraideth not; and it shall be given him."),
    ("Psalm 121:1-2", "I will lift up mine eyes unto the hills, from whence cometh my help. My help cometh from the LORD, which made heaven and earth."),
    ("Deuteronomy 31:6", "Be strong and of a good courage, fear not, nor be afraid of them: for the LORD thy God, he it is that doth go with thee; he will not fail thee, nor forsake thee."),
    ("Matthew 11:28", "Come unto me, all ye that labour and are heavy laden, and I will give you rest."),
    ("Psalm 90:17", "And let the beauty of the LORD our God be upon us: and establish thou the work of our hands upon us; yea, the work of our hands establish thou it."),
    ("Proverbs 18:15", "The heart of the prudent getteth knowledge; and the ear of the wise seeketh knowledge."),
    ("Lamentations 3:22-23", "It is of the LORD's mercies that we are not consumed, because his compassions fail not. They are new every morning: great is thy faithfulness."),
    ("Psalm 27:1", "The LORD is my light and my salvation; whom shall I fear? the LORD is the strength of my life; of whom shall I be afraid?"),
    ("Ecclesiastes 9:10", "Whatsoever thy hand findeth to do, do it with thy might."),
    ("Nehemiah 8:10", "...for the joy of the LORD is your strength."),
    ("Hebrews 12:1", "...let us run with patience the race that is set before us."),
    ("Psalm 145:18", "The LORD is nigh unto all them that call upon him, to all that call upon him in truth."),
    ("Proverbs 11:14", "Where no counsel is, the people fall: but in the multitude of counsellors there is safety."),
    ("Isaiah 26:3", "Thou wilt keep him in perfect peace, whose mind is stayed on thee: because he trusteth in thee."),
    ("Micah 6:8", "...and what doth the LORD require of thee, but to do justly, and to love mercy, and to walk humbly with thy God?"),
    ("Psalm 16:8", "I have set the LORD always before me: because he is at my right hand, I shall not be moved."),
    ("Romans 12:12", "Rejoicing in hope; patient in tribulation; continuing instant in prayer."),
    ("Proverbs 4:23", "Keep thy heart with all diligence; for out of it are the issues of life."),
    ("1 Peter 5:7", "Casting all your care upon him; for he careth for you."),
    ("Psalm 28:7", "The LORD is my strength and my shield; my heart trusted in him, and I am helped."),
]


def verse_of_the_day(today: datetime.date | None = None) -> tuple[str, str]:
    """Deterministic verse for a given date — rotates through the list yearly."""
    today = today or datetime.date.today()
    return VERSES[today.timetuple().tm_yday % len(VERSES)]


def random_verse(seed: int | None = None) -> tuple[str, str]:
    """A verse chosen without the date. ``seed`` makes it deterministic if given."""
    if seed is None:
        # Avoid importing random for one pick; fold the clock into an index.
        seed = int(datetime.datetime.now().strftime("%H%M%S%f"))
    return VERSES[seed % len(VERSES)]


def format_daily(today: datetime.date | None = None) -> str:
    ref, text = verse_of_the_day(today)
    return f"📖 *Daily Scripture* — {ref}\n\n“{text}”\n\nHave a blessed day. 🌅"
