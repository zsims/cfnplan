from enum import Enum


class Change(Enum):
    added = 0
    removed = 1
    changed = 2

class TemplateDiff(object):
    def __init__(self, before, after):
        self.before = before
        self.after = after

    def build(self):
        for top_element in self.before.elements:
            self._build(top_element)

    def _build(self, top_element):
        if top_element.

