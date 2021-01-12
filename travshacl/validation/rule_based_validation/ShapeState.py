# -*- coding: utf-8 -*-
__author__ = "Monica Figuera"


class ShapeState:
    def __init__(self, shape):
        self.inferred_rule_atoms = {}
        self.pending_refs_to_saturate = set(shape.referencedShapes.keys())
        self.remaining_targets_count = 0
        self.rule_map = {}
        self.rule_count = 0
        self.validated_targets = set()
        self.invalidated_targets = set()

    def add_inferred_atom(self, atom, is_rule_head):
        self.inferred_rule_atoms[atom] = {"is_rule_head": is_rule_head}

    def exists_inferred_atom(self, atom):
        return self.inferred_rule_atoms.get(atom) is not None

    def get_pending_refs_to_saturate(self):
        return self.pending_refs_to_saturate

    def remove_saturated_referenced_shape(self, shape_name):
        return self.pending_refs_to_saturate.discard(shape_name)

    def set_initial_targets_count(self, k):
        self.remaining_targets_count = k

    def get_remaining_targets_count(self):
        return self.remaining_targets_count

    def decrease_remaining_targets_count(self):
        self.remaining_targets_count -= 1

    def add_shape_rule(self, head, body):
        if self.rule_map.get(head) is None:
            s = set()
            s.add(body)
            self.rule_map[head] = s
        else:
            self.rule_map[head].add(body)

    def get_rule_map(self):
        return self.rule_map

    def is_rule_head(self, a):
        return self.rule_map.get(a) is not None

    def increase_rule_count(self):
        self.rule_count += 1

    def get_rule_count(self):
        return self.rule_count

    def add_validated_target(self, t):
        self.validated_targets.add(t)

    def get_validated_targets(self):
        return self.validated_targets

    def add_invalidated_target(self, t):
        self.invalidated_targets.add(t)

    def get_invalidated_targets(self):
        return self.invalidated_targets
