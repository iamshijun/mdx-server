if sys.version_info < (3, 0, 0):
    from pattern.en import lemma
else:
    pass

import sys

if __name__=="__main__":
    if len(sys.argv) < 1 :
        print "lemma.py word"
        exit(0)
    word=sys.argv[1]
    print lemma(word)
