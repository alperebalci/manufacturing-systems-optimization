import unittest
from study import fixture,plan,audit,exhaustive,Action
class PlanningTests(unittest.TestCase):
    def test_exact(self):
        args=fixture();r=plan(*args);self.assertEqual((r['makespan'],r['cost']),exhaustive(*args))
    def test_resource_outage_changes_plan(self):
        A,I,G,C,H=fixture();before=plan(A,I,G,C,H);C['vendor']=[0]*H;after=plan(A,I,G,C,H)
        self.assertIn('buy_A',before['starts']);self.assertNotIn('buy_A',after['starts'])
        self.assertEqual((after['makespan'],after['cost']),exhaustive(A,I,G,C,H))
    def test_freeze(self):
        args=fixture();r=plan(*args,fixed={'cut_A':0},earliest_new_start=1)
        self.assertEqual(r['starts']['cut_A'],0)
        self.assertTrue(all(t>=1 for a,t in r['starts'].items() if a!='cut_A'))
    def test_impossible_goal(self):
        A,I,G,C,H=fixture();self.assertEqual(plan(A,I,{'unknown'},C,H)['status'],'infeasible')
    def test_bad_precedence(self):
        A,I,G,C,H=fixture();self.assertFalse(audit(A,{'cut_A':0,'cut_B':2,'assemble':1},I,G,C,H))
    def test_cycle_cannot_self_support(self):
        A=[Action('a',frozenset({'b'}),frozenset({'a'}),1,'r'),Action('b',frozenset({'a'}),frozenset({'b'}),1,'r')]
        self.assertEqual(plan(A,set(),{'a'},{'r':[2]*3},3)['status'],'infeasible')
    def test_invalid(self):
        A,I,G,C,H=fixture();C['mill']=[1]
        with self.assertRaises(ValueError):plan(A,I,G,C,H)
if __name__=='__main__':unittest.main()
