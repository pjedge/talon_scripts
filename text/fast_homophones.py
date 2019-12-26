from talon import app, clip, cron, resource
from talon.voice import Context, Str, press
from ..misc.basic_keys import digits, alphabet, get_keys

from ..utils import insert

import os

# the alignment score of two strings
# end gaps are not penalized on either string
# score of +1 for matching letters and uniform penalty of -1 for mismatch and gap
# alignment_score('word', 'worms') == 2
# alignment_score('word', 'sword') == 4
def alignment_score(seq1, seq2):

    sigma = -1
    n = len(seq1)+1
    m = len(seq2)+1

    scores = [[0]*m for v in range(n)]

    for i in range(1,n):
        for j in range(1,m):

            s1 = seq1[i-1]
            s2 = seq2[j-1]
            match_score = 1 if s1 == s2 else -1
            options = [scores[i-1][j-1] + match_score,
                       scores[i][j-1]   + sigma,
                       scores[i-1][j]   + sigma]

            score = max(options)

            scores[i][j] = score

    return max(list(scores[-1]) + [row[-1] for row in scores])

########################################################################
# global settings
########################################################################

# a list of homophones where each line is a comma separated list
# e.g. where,wear,ware
# a suitable one can be found here:
# https://github.com/pimentel/homophones
cwd = os.path.dirname(os.path.realpath(__file__))
homophones_file = os.path.join(cwd, "homophones.csv")
# if quick_replace, then when a word is selected and only one homophone exists,
# replace it without bringing up the options
quick_replace = True
########################################################################

context = Context("fast_homophones")

phones = {}
canonical = []
with resource.open(homophones_file, "r") as f:
    for h in f:
        h = h.rstrip()
        h = h.split(",")
        canonical.append(max(h, key=len))
        for w in h:
            w = w.lower()
            others = phones.get(w, None)
            if others is None:
                phones[w] = sorted(h)
            else:
                # if there are multiple hits, collapse them into one list
                others += h
                others = set(others)
                others = sorted(others)
                phones[w] = others

# the user says "phony <word1> <word2>"
# this function inserts the homophone of <word1> that is most similar to <word2>
# in terms of the alignment score
#
# For Example:
# "phony check czechoslovakia"  -> inserts Czech
# "phony check zebra"  -> inserts Czech
# "phony check checking"  -> inserts check
# "phony check cap krunch"  -> inserts check

def pick_similar_homophones(m):

    words = m.dgndictation[0]._words
    alpha = [''.join(get_keys(m))]
    if len(alpha[0]) == 0:
        alpha = []

    if len(words)+len(alpha) != 2:
        return

    word1 = words[0]
    word2 = words[1] if len(words) == 2 else alpha[0]

    if word1 not in phones:
        return

    options = phones[word1]
    _, max_option = max([(alignment_score(o, word2), o) for o in options],key=lambda x: x[0])

    insert(max_option)

context.keymap(
    {
        "phony <dgndictation> {basic_keys.alphabet}* [over]": pick_similar_homophones,
    }
)
