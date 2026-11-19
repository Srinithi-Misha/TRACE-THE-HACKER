import random
import xml.etree.ElementTree as ET
from collections import deque

class DFA:
    def __init__(self, path):
        root = ET.parse(path).getroot()
        self.names, self.delta, self.finals = {}, {}, set()
        self.initial = None
        for s in root.iter("state"):
            sid = s.get("id")
            self.names[sid] = s.get("name")
            if s.find("initial") is not None: self.initial = sid
            if s.find("final") is not None: self.finals.add(sid)
        for t in root.iter("transition"):
            self.delta[(t.findtext("from"), t.findtext("read"))] = t.findtext("to")
        self.alphabet = sorted({x[1] for x in self.delta})
        self.trap = next(i for i, name in self.names.items() if name == "TRAP")

    def run(self, sequence):
        state, steps, trap = self.initial, [], None
        for i, symbol in enumerate(sequence, 1):
            nxt = self.delta[(state, symbol)]
            steps.append({"from": state, "to": nxt})
            if nxt == self.trap and trap is None: trap = i
            state = nxt
        return {"steps": steps, "end": state,
                "accepted": state in self.finals, "trap_step": trap}

    def labels(self, seed):
        other = [s for s in self.names if s not in (self.initial, self.trap)]
        random.Random(seed).shuffle(other)
        return {self.initial: "S0", self.trap: "TRAP",
                **{s: f"S{i}" for i, s in enumerate(other, 1)}}

    def shortest_accepted(self):
        queue, seen = deque([(self.initial, "")]), {self.initial}
        while queue:
            state, word = queue.popleft()
            if state in self.finals: return word
            for symbol in self.alphabet:
                nxt = self.delta[(state, symbol)]
                if nxt != self.trap and nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, word + symbol))
        return ""
