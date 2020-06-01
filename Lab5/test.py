import copy
import operator
import functools
import itertools
from collections import defaultdict
import math

import cProfile

import pandas as pd
from blist import blist, sortedlist, sortedset
from sklearn.preprocessing import LabelEncoder

timeslots = pd.read_csv('data/timeslots.csv').iloc[:,0].values.tolist()

lecs = pd.read_csv('data/lecteurs.csv')
lele = LabelEncoder()
lecs['Prof'] = lele.fit_transform(lecs['Prof'])
lg = lecs.groupby(['Lesson', 'Lecteur'])['Prof'].apply(list).to_dict()

rooms = pd.read_csv('data/rooms.csv')
lrs = rooms['Aud'][rooms['Lecture']].values.tolist()
nlrs = rooms['Aud'][~rooms['Lecture']].values.tolist()
isrlec = {True: lrs, False: nlrs}

plan = pd.read_csv('data/plan.csv')
plan, counts = plan.drop(columns=['count']), plan['count']

entries = list(itertools.chain.from_iterable([tuple(e)] * c for e, c in zip(plan.values, counts)))

group_index = defaultdict(sortedlist)
lesson_index = defaultdict(sortedlist)
for idx, entry in enumerate(entries):
    group_index[entry[0]].add(idx)
    lesson_index[entry[1:]].add(idx)

iterations = 0

class ScheduleDomain:
    def __init__(self, copy=False):
        if copy: return
        self.timeslot_index = defaultdict(sortedlist)
        self.domains = blist([])
        for entry in entries: self.domains.append((sortedlist(timeslots), sortedlist(isrlec[entry[2]]), sortedlist(lg[entry[1:]])))
        self.adomain = blist([set() for e in entries])
        self.akill_list = blist([defaultdict(sortedlist) for e in entries])
        self.lkill_list = blist([defaultdict(sortedlist) for e in entries])
        self.asses = blist([None for e in entries])
        self.unassigned = set(range(len(entries)))
        for timeslot in timeslots:
            self.timeslot_index[timeslot] = sortedlist(self.unassigned)

    def __deepcopy__(self, memo):
        cls = self.__class__
        res = cls.__new__(cls)

        res.timeslot_index = self.timeslot_index.copy()
        for k, v in res.timeslot_index.items():
            res.timeslot_index[k] = sortedlist(v)

        res.domains = self.domains.copy()
        for idx, val in enumerate(res.domains):
            res.domains[idx] = (sortedlist(val[0]), sortedlist(val[1]), sortedlist(val[2]))

        res.adomain = self.adomain.copy()
        for idx, val in enumerate(res.adomain):
            res.adomain[idx] = val.copy()

        res.akill_list = self.akill_list.copy()
        for idx, val in enumerate(res.akill_list):
            res.akill_list[idx] = val.copy()
        res.lkill_list = self.lkill_list.copy()
        for idx, val in enumerate(res.lkill_list):
            res.lkill_list[idx] = val.copy()

        res.asses = self.asses.copy()
        res.unassigned = self.unassigned.copy()
        return res

    def assign(self, idx, timeslot, aud, lecteur):
        global iterations
        iterations += 1
        if iterations % 100 == 0:
            print(iterations, 'iterations', math.floor(math.log(self.assignment_count(), 2)), len(self.unassigned), (timeslot, aud, lecteur))
            if iterations % 1000 == 0:
                print([(idx, d) for idx, d in enumerate(self.domains) if idx in self.unassigned])
        d2 = copy.deepcopy(self)
        d2.unassigned.remove(idx)
        for nidx in group_index[entries[idx][0]]:
            if nidx in d2.unassigned:
                d2.domains[nidx][0].discard(timeslot)
                d2.timeslot_index[timeslot].discard(nidx)
                if timeslot in d2.akill_list[nidx]: d2.akill_list[nidx].pop(timeslot)
                if timeslot in d2.lkill_list[nidx]: d2.lkill_list[nidx].pop(timeslot)
        for iidx in d2.timeslot_index[timeslot]:
            if iidx in d2.unassigned:
                d2.akill_list[nidx][timeslot].add(aud)
                d2.lkill_list[nidx][timeslot].add(lecteur)
                d2.domains[iidx][2].discard(lecteur)
        if entries[idx][2]:
            for iidx in lesson_index[entries[idx][1:]]:
                if iidx in d2.unassigned:
                    d2.adomain[iidx].add((timeslot, aud, lecteur))
        d2.domains[idx] = ([],[],[])
        d2.asses[idx] = (timeslot, aud, lecteur)
        d2.adomain[idx].clear()
        return d2

    def kill_count(self, idx, ass):
        kills = 0
        for nidx in group_idx[entries[idx][0]]:
            if ass[0] in self.domains[nidx][0] and nidx in self.unassigned and nidx != idx:
                kills += len(self.domains[nidx][1]) * len(self.domains[nidx][2])
        for nidx in self.timeslot_index[ass[0]]:
            if nidx == idx or ind not in self.unassigned: continue
            kill_count += len(self.domains[nidx][1]) + len(self.domains[nidx][2]) - 1

    def is_consistent(self):
        return all(map(self.get_ass_count, self.unassigned))

    def get_ass_count(self, ei):
        base_count = functools.reduce(operator.mul, map(len, self.domains[ei])) + len(self.adomain[ei])
        for timeslot in self.domains[ei][0]:
            akilled_count = len(self.akill_list[ei][timeslot]) * len(self.domains[ei][2])
            lkilled_count = len(self.lkill_list[ei][timeslot]) * len(self.domains[ei][1])
            base_count -= akilled_count + lkilled_count - len(self.akill_list[ei][timeslot]) * len(self.lkill_list[ei][timeslot])
        return base_count

    def assignment_count(self):
        return functools.reduce(operator.mul, map(self.get_ass_count, self.unassigned))

    def get_lcv_entry_assignments(self, idx):
        entras = self.get_entry_assignments(idx)
        return sorted(entras, key=lambda e: self.kill_count(idx, e))

    def get_raw_entry_assignments(self, idx):
        if len(self.adomain[idx]):
            try:
                yield from iter(self.adomain[idx])
            except:
                pass
        yield from itertools.product(*self.domains[idx])

    def get_entry_assignments(self, idx):
        for e in self.get_raw_entry_assignments(idx):
            if e[1] not in self.akill_list[idx][e[0]] and e[2] not in self.lkill_list[idx][e[0]]:
                yield e

    def get_assignments(self):
        for una in self.unassigned: yield from self.get_entry_assignments(una)

    def get_mrv_entries(self):
        yield from sorted(self.unassigned, key=self.get_ass_count)

    def get_entries(self):
        yield from self.unassigned

    def to_result(self):
        ret = pd.DataFrame([entry + self.asses[idx] for idx, entry in enumerate(entries)],
            columns=['Group', 'Lesson', 'Lecture', 'Timeslot', 'Aud', 'Prof'])
        ret['Prof'] = lele.inverse_transform(ret['Prof'])
        return ret

def solve(domain):
    for en in domain.get_mrv_entries():
        for ass in domain.get_entry_assignments(en):
            newsol = domain.assign(en, *ass)
            if not newsol.is_consistent(): continue
            if len(newsol.unassigned) == 0: return newsol
            s = solve(newsol)
            if not s: continue
            if len(s.unassigned) == 0: return s

domain = ScheduleDomain()

print(solve(domain).to_result())
print('Found soluion in', iterations, 'iterations')
