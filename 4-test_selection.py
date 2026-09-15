import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from ravenclip import Segment, score_window, choose, Candidate
class SelectionTests(unittest.TestCase):
    def test_hooks_score_above_plain_text(self):
        hooked=[Segment(0,15,"Why does this fail? The key mistake costs 30 percent."),Segment(15,30,"Here is the surprising reason and the best fix.")]
        plain=[Segment(0,15,"The speaker continues talking about the general topic."),Segment(15,30,"There is some additional information in this section.")]
        self.assertGreater(score_window(hooked,0,30).score, score_window(plain,0,30).score)
    def test_overlap_suppression(self):
        rows=[Candidate(0,30,9,"a",[]),Candidate(5,35,8,"b",[]),Candidate(40,70,7,"c",[])]
        self.assertEqual([(x.start,x.end) for x in choose(rows,2)],[(0,30),(40,70)])
if __name__ == '__main__': unittest.main()
