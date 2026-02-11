"""
scripts/sentiment_lexicon.py

Financial domain-specific sentiment lexicon for word-bank sentiment analysis.

Contains:
- Sentiment word lists (strong/moderate/weak, positive/negative)
- Intensity modifiers (multiply base scores)
- Negation words (flip polarity)
"""

# Strong positive sentiment words (score: +2)
STRONG_POSITIVE = [
    'surge', 'soar', 'rally', 'rocket', 'skyrocket', 'explode', 'breakthrough',
    'record high', 'all-time high', 'peak', 'milestone',
    'outperform', 'outperforming', 'beat', 'beats', 'beating', 'exceed',
    'upside', 'bullish', 'bull market', 'bull run', 'soars', 'soaring',
    'momentum', 'strength', 'strong', 'robust', 'solid', 'impressive','new highs', 'all-time highs', 'all-time high',
    'upgrade', 'upgrades','upgraded', 'buy', 'buys', 'bought', 'buy rating', 'strong buy', 'outperform rating',
    'surpasses', 'surpassing', 'surpass', 'surpassed',
]

# Moderate positive sentiment words (score: +1)
MODERATE_POSITIVE = [
    'approves', 'secures', 'wins', 'expands', 'raises', 'beats', 'rise', 'rises', 'unveils', 'unveil', 'rising', 'gain', 'gains', 'gaining', 'climb', 'climbs',
    'climbing', 'jump', 'jumps', 'jumping', 'increase', 'increases', 'increasing',
    'up', 'upside', 'growth', 'growing', 'expand', 'expands', 'expansion',
    'positive', 'optimistic', 'optimism', 'confidence', 'confident', 'grow', 'grows',
    'improve', 'improves', 'improving', 'improvement', 'better', 'best',
    'profit', 'profits', 'profitable', 'profitability', 'earnings beat', 'new high',
    'revenue growth', 'margin expansion', 'guidance raise', 'guidance raised',
    'momentum', 'trending up', 'uptrend', 'support', 'resistance break',
]

# Weak positive sentiment words (score: +0.5)
WEAK_POSITIVE = [
    'stable', 'stability', 'steady', 'steadily', 'maintain', 'maintains',
    'hold', 'holds', 'holding', 'neutral', 'neutral rating', 'hold rating',
    'modest', 'modestly', 'slight', 'slightly', 'gradual', 'gradually',
]

# Weak negative sentiment words (score: -0.5)
WEAK_NEGATIVE = [
    'concern', 'concerns', 'concerned', 'caution', 'cautious', 'uncertainty',
    'uncertain', 'volatile', 'volatility', 'fluctuation', 'fluctuations',
    'modest decline', 'slight dip', 'slight drop' 
]

# Moderate negative sentiment words (score: -1)
MODERATE_NEGATIVE = [
    'fall', 'falls', 'falling', 'drop', 'drops', 'dropping', 'decline', 'declines',
    'declining', 'decrease', 'decreases', 'decreasing', 'down', 'downside', 'loses', 'losing',
    'loss', 'losses', 'negative', 'pessimistic', 'pessimism', 'warning',
    'warnings', 'warning sign', 'warning signs', 'lawsuit', 'miss', 'misses',
    'investigation', 'investigates', 'probe', 'antitrust', 'regulation',
    'regulatory',
    'worry', 'worries', 'worried', 'fear', 'fears', 'fearful', 'debt', 'debts', 'debt load', 'debt burden', 'debt crisis', 'debt crisis',
    'dip', 'dips', 'dipped', 'slip', 'slips', 'slipping', 'slide', 'slides',
    'tumble', 'tumbles', 'tumbling', 'sink', 'sinks', 'sinking', 'tighten', 'tightens', 'tightening', 'tightenings', 'tighten up', 'tightenings up', 'tighten up', 'tightenings up',
    'earnings miss', 'revenue decline', 'margin compression', 'guidance cut', 'miss', 'misses', 'missing', 'missed', 'missed estimates', 'missed expectations', 'missed forecast', 'missed projection', 'missed target', 'missed guidance', 'missed estimate', 'missed forecast', 'missed projection', 'missed target', 'missed guidance',
    'guidance lowered', 'downgrade', 'downgraded', 'sell rating',
    'underperform', 'wither', 'withers', 'perish', 'perishes'
]

# Strong negative sentiment words (score: -2)
STRONG_NEGATIVE = [
    'crash', 'crashes', 'crashing', 'plunge', 'plunges', 'plunging',
    'collapse', 'collapses', 'collapsing', 'collapse', 'crisis', 'crises',
    'bearish', 'bear market', 'bear run', 'correction', 'corrections',
    'selloff', 'sell-off', 'sell off', 'rout', 'routs', 'panic', 'panics',
    'disappoint', 'disappoints', 'disappointing', 'disappointment',
    'failure', 'failures', 'fails', 'failed', 'failing', 'die', 'dies'
    'worst', 'worst-performing', 'underperform', 'underperforming',
    'breakdown', 'break down', 'support break', 'resistance break down',
]

# Intensity modifiers (multiply base score)
INTENSITY_MODIFIERS = {
    'very': 1.5,
    'extremely': 2.0,
    'highly': 1.5,
    'significantly': 1.5,
    'substantially': 1.5,
    'dramatically': 2.0,
    'slightly': 0.5,
    'somewhat': 0.75,
    'moderately': 0.75,
    'marginally': 0.5,
}

# Negation words (flip polarity)
NEGATION_WORDS = [
    'not', 'no', 'never', 'none', 'nothing', 'nobody', 'nowhere',
    'neither', 'nor', "n't", "don't", "doesn't", "didn't", "won't",
    "can't", "couldn't", "shouldn't", "wouldn't", "isn't", "aren't",
    "wasn't", "weren't", "hasn't", "haven't", "hadn't",
]
