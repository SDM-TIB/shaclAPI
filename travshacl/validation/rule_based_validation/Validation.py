# -*- coding: utf-8 -*-
__author__ = "Monica Figuera"

from validation.utils import fileManagement
from validation.utils.RuleBasedValidStats import RuleBasedValidStats
from validation.utils import SHACL2SPARQLEvalOrder
from validation.core.Literal import Literal
from validation.rule_based_validation.InstancesRetrieval import InstancesRetrieval
from validation.rule_based_validation.ShapeState import ShapeState
import time


class Validation:
    def __init__(self, endpoint_URL, node_order, shapes_dict, option, target_shape_predicates, selectivity_enabled,
                 use_SHACL2SPARQL_order, log_output, valid_output, invalid_output, stats_output, traces_output):

        if use_SHACL2SPARQL_order:
            dataset = 'LUBM'
            self.node_order = SHACL2SPARQLEvalOrder.get_node_order(dataset, len(shapes_dict))
        else:
            self.node_order = node_order

        self.shapes_dict = shapes_dict
        self.set_parent_shapes()
        self.eval_inst_type = option  # possible values: 'valid', 'violated', 'all'
        self.target_shape_predicates = target_shape_predicates
        self.selectivity_enabled = selectivity_enabled  # use selective queries

        self.log_output = log_output
        self.valid_output = valid_output
        self.violated_output = invalid_output
        self.stats_output = stats_output
        self.stats = RuleBasedValidStats()

        self.log_output.write("Node order: " + str(self.node_order) + '\n')
        self.traces_output = traces_output
        self.start_of_verification = time.time() * 1000.0
        self.traces_output.write("Target, #TripleInThatClass, TimeSinceStartOfVerification(ms)\n")

        self.inst_retrieval = InstancesRetrieval(endpoint_URL, shapes_dict, self.log_output, self.stats)
        self.save_output_to_file = True

    def set_parent_shapes(self):
        for shape_name in self.shapes_dict:
            child_shapes = self.shapes_dict[shape_name].referencedShapes
            for child_name in child_shapes:
                self.shapes_dict[child_name].addParentShape(shape_name)

    def write_targets_to_file(self, state):
        """
        Saves to local file the new validated target

        :param state:
        :return:
        """
        if self.eval_inst_type == "valid" or self.eval_inst_type == "all":
            for valid in state.valid_targets:
                self.valid_output.write(valid)

        if self.eval_inst_type == "violated" or self.eval_inst_type == "all":
            for invalid in state.invalid_targets:
                self.violated_output.write(invalid)

        for trace in state.traces:
            self.traces_output.write(trace)

    def retrieve_validation_output(self, state):
        no_shape_name = "NoShape"
        output = {shape_name: {
                        "valid_instances": state.shapes_state[shape_name].get_validated_targets(),
                        "invalid_instances": state.shapes_state[shape_name].get_invalidated_targets(),
                 } for shape_name in self.shapes_dict.keys()}

        output[no_shape_name] = {"valid_instances": state.get_valid_targets_after_termination()}
        return output

    def exec(self):
        focus_shape = self.shapes_dict[self.node_order.pop(0)]  # first shape to be evaluated
        depth = 0  # evaluation order
        initial_targets = self.inst_retrieval.extract_target_atoms(focus_shape)
        all_shapes_state = {shape_name: ShapeState(self.shapes_dict[shape_name])
                            for shape_name in self.shapes_dict.keys()}

        self.log_output.write("Retrieving (initial) targets ...")
        self.log_output.write("\nTargets retrieved.")
        self.log_output.write("\nNumber of targets: " + str(len(initial_targets)))
        self.stats.recordInitialTargets(str(len(initial_targets)))
        start = time.time() * 1000.0
        state = EvalState(all_shapes_state, initial_targets)
        state.shapes_state[focus_shape.getId()].set_initial_targets_count(len(initial_targets))
        self.validate(
            state,
            depth,
            focus_shape
        )
        finish = time.time() * 1000.0
        elapsed = round(finish - start)
        self.stats.recordTotalTime(elapsed)
        print("Total execution time: ", str(elapsed), " ms")
        self.log_output.write("\nTotal number of rules: " + str(self.stats.totalRuleNumber))
        self.log_output.write("\nMaximal number or rules in memory: " + str(self.stats.maxRuleNumber))

        if self.save_output_to_file:
            self.write_targets_to_file(state)
            self.stats.writeAll(self.stats_output)

        fileManagement.closeFile(self.valid_output)
        fileManagement.closeFile(self.violated_output)
        fileManagement.closeFile(self.stats_output)
        fileManagement.closeFile(self.log_output)

        return self.retrieve_validation_output(state)

    def register_target(self, t, is_valid, depth, log_message, shape_name, state):
        """
        Adds each target to the set of valid/invalid instances of the shape.

        :param t: target
        :param is_valid: boolean value that tells if 't' is a valid or a violated instance
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param log_message:
        :param shape_name: name of the shape that contains the target 't'
        :param state:
        """
        f_shape_str = ", focus shape " + shape_name
        log = t.getStr() + ", depth " + str(depth) + f_shape_str + ", " + log_message + "\n"

        instance = "<" + t.getArg() + ">"

        if is_valid:
            if shape_name == '':
                state.add_valid_target_after_termination(t)
            else:
                self.shapes_dict[t.getPredicate()].bindings.add(instance)
                state.shapes_state[shape_name].add_validated_target(t)

            state.valid_targets.add(log)
        else:
            self.shapes_dict[t.getPredicate()].invalidBindings.add(instance)
            state.invalid_targets.add(log)
            state.shapes_state[shape_name].add_invalidated_target(t)

        target_type = "valid" if is_valid else "violated"
        trace_log = target_type + ", " + \
                    str(state.traces_count) + ", " + \
                    str(round(time.time() * 1000.0 - self.start_of_verification)) + "\n"

        state.traces.add(trace_log)
        state.traces_count += 1

    @staticmethod
    def is_satisfiable(a, state, shape_name):
        atom_in_eval_preds = a.getPredicate() in state.evaluated_predicates
        atom = a.getAtom()

        is_rule_head = state.shapes_state[shape_name].is_rule_head(atom)
        is_inferred = state.shapes_state[shape_name].exists_inferred_atom(atom)

        return not atom_in_eval_preds or is_rule_head or is_inferred

    def eval_binding(self, binding, state, shape_name, rule_head, rule_pattern_body):
        """
        For each rule pattern, perform (1), (2), (3):
        # step (1) - derive negative information:
                For any (possibly negated) atom 'a', we verify if it is not satisfiable
                => infer the negation of the atom
        # step (2) - infer rule:
                If the negation of any rule body has already been inferred
                => the rule cannot be satisfied, we don't add it to rule_map, and infer the negation of the rule head
        # step (3) - add pending rule to rule_map for future classification / classify (if candidate valid target)

        :param binding: instance retrieved from the endpoint
        :param state:
        :param shape_name: string with the name of the shape currently being evaluated
        :param rule_head: grounded rule head
        :param rule_pattern_body: ungrounded rule body
        :return:
        """
        is_candidate_valid_target = rule_head.getPredicate() in self.target_shape_predicates \
                                    and rule_head in state.remaining_targets
        body = set()
        is_body_inferred = False
        focus_shape_state = state.shapes_state[shape_name]
        for atom_pattern in rule_pattern_body:
            atom_shape_name = atom_pattern.getPredicate().split("_")[0]
            body_atom_shape_state = state.shapes_state[atom_shape_name]
            a = Literal(atom_pattern.getPredicate(), binding[atom_pattern.getArg()]["value"], atom_pattern.getIsPos())
            body.add(a)
            if body_atom_shape_state.is_rule_head(a):
                if not body_atom_shape_state.exists_inferred_atom(a):  # if item not inferred yet
                    # step (1) - negate (unmatchable body atoms)
                    if not self.is_satisfiable(a, state, atom_shape_name):
                        negated_atom = a.getNegation() if a.getIsPos() else a  # eg, !Department_d1_max...
                        body_atom_shape_state.add_inferred_atom(negated_atom, False)

                        # step (2) - infer negation of rule head (from negation of rule body atom)
                        focus_shape_state.add_inferred_atom(rule_head.getNegation(), False)

                        # step (3) - classify invalid target
                        if rule_head.getIsPos() and is_candidate_valid_target:
                            self.register_target(rule_head, False, "collection (negated body)", "", shape_name, state)
                            state.remaining_targets.discard(rule_head)
                            focus_shape_state.decrease_remaining_targets_count()
                            return

                        is_body_inferred = True  # infer only when a body atom is not satisfiable
                        break  # negated body atom means the rule cannot be inferred -> halt the loop (short-circuit)

        # step (3) - add pending rule / classify valid target
        if not is_body_inferred:
            focus_shape_state.add_shape_rule(rule_head, frozenset(body))
            focus_shape_state.increase_rule_count()
        else:
            focus_shape_state.add_inferred_atom(rule_head, True)  # infer rule head
            focus_shape_state.increase_rule_count()

            if is_candidate_valid_target:
                self.register_target(rule_head, True, "collection", "", shape_name, state)
                state.remaining_targets.discard(rule_head)
                focus_shape_state.decrease_remaining_targets_count()

    def ground_and_saturate(self, binding, state, shape, query_rule_pattern, shape_rule_pattern):
        """
        Rules given by
          - query rule pattern (of the current evaluated constraint query)
          - and shape rule pattern (shape for which the constraint query was evaluated)
        are going to be grounded (instantiated) with instances retrieved from the endpoint.

        :param binding: instance retrieved from the endpoint
        :param state:
        :param shape: current shape being evaluated
        :param query_rule_pattern: query rule pattern
        :param shape_rule_pattern: shape rule pattern
        :return:
        """
        shape_name = shape.getId()

        query_RP_head = query_rule_pattern.getHead()
        shape_RP_head = shape_rule_pattern.getHead()

        query_rule_head = Literal(query_RP_head.getPredicate(),
                                  binding[query_RP_head.getArg()]["value"],
                                  query_RP_head.getIsPos())
        shape_rule_head = Literal(shape_RP_head.getPredicate(),
                                  binding[shape_RP_head.getArg()]["value"],
                                  shape_RP_head.getIsPos())

        self.eval_binding(binding, state, shape_name, query_rule_head, query_rule_pattern.getBody())
        self.eval_binding(binding, state, shape_name, shape_rule_head, shape_rule_pattern.getBody())

    def negate_unmatchable_heads(self, state, depth, rule_map, shape_invalidating_name):
        """
        This procedure derives negative information
        For any (possibly negated) atom 'a' that is either a target or appears in some rule, we may be able
        to infer that 'a' cannot hold (it is not satisfiable):
          if 'a' is not inferred yet,
          if the query has already been evaluated,
          and if there is not rule with 'a' as its head.
        Thus, in such case, 'not a' is added to the inferred atoms of the corresponding shape.

        :param state:
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param rule_map: set of rules corresponding to the focus shape
        :param shape_invalidating_name: name of the shape that started the saturation at level 'depth' before recursion
        :return: True is new unsatisfied rule head literals were found, False otherwise
        """
        all_body_atoms = set(frozenset().union(*set().union(*rule_map.values())))
        new_negated_atom_found = False
        for a in all_body_atoms:
            atom_shape_name = a.getPredicate().split("_")[0]  # e.g., Department_d1_pos -> Department
            if not self.is_satisfiable(a, state, atom_shape_name):
                negated_atom = a.getNegation() if a.getIsPos() else a  # e.g., !Department_d1_max_...
                if not state.shapes_state[atom_shape_name].exists_inferred_atom(negated_atom):
                    new_negated_atom_found = True
                    state.shapes_state[atom_shape_name].add_inferred_atom(negated_atom, False)

        remaining = set()
        for t in state.remaining_targets:
            shape_name = t.getPredicate()
            if not self.is_satisfiable(t, state, shape_name):
                self.register_target(t, False, depth, "negated unmatchable rule head", shape_invalidating_name, state)
                state.shapes_state[shape_name].add_inferred_atom(t.getNegation(), False)
                state.shapes_state[shape_name].decrease_remaining_targets_count()
            else:
                remaining.add(t)

        state.remaining_targets = remaining

        return new_negated_atom_found

    def apply_rules(self, state, depth, rule_map, shape_invalidating_name):
        """
        INFER procedure performs 2 types of inferences:
        # case (1): If the set of rules contains a rule and each of the rule bodies has already been inferred
                    => head of the rule is inferred, rule dropped.
        # case (2): If the negation of any rule body has already been inferred
                    => this rule cannot be applied (rule head not inferred) so the entire rule is dropped.

        :param state:
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param rule_map:
        :param shape_invalidating_name: name of the shape that started the saturation at level 'depth' before recursion
        :return: True if new inferences were found, False otherwise
        """
        fresh_literals = False
        rule_map_copy = rule_map.copy()
        for head in rule_map_copy:
            bodies = rule_map[head]
            head_shape_name = head.getPredicate().split("_")[0]
            for body in bodies:
                is_body_inferred = True
                for a in body:
                    atom_shape_name = a.getPredicate().split("_")[0]
                    if not state.shapes_state[atom_shape_name].exists_inferred_atom(a):
                        is_body_inferred = False

                        # case (2)
                        if state.shapes_state[atom_shape_name].exists_inferred_atom(a.getNegation()):
                            if head in state.remaining_targets:
                                self.register_target(head, False, depth, "negated rule body", shape_invalidating_name, state)
                                state.remaining_targets.discard(head)
                                state.shapes_state[head_shape_name].decrease_remaining_targets_count()
                            state.shapes_state[head_shape_name].add_inferred_atom(head.getNegation(), False)

                            if rule_map.get(head) is not None:
                                del rule_map[head]
                            break
                # case (1)
                if is_body_inferred:
                    fresh_literals = True

                    if head in state.remaining_targets:
                        self.register_target(head, True, depth, "", shape_invalidating_name, state)
                        state.remaining_targets.discard(head)
                        state.shapes_state[head_shape_name].decrease_remaining_targets_count()
                    # e.g., University(...), University_d1_pos(...)
                    state.shapes_state[head_shape_name].add_inferred_atom(head, True)

                    if rule_map.get(head) is not None:
                        del rule_map[head]
                    break

        if not fresh_literals:
            return False

        self.log_output.write("\nRemaining targets: " + str(len(state.remaining_targets)))
        return True

    def saturate_remaining(self, state, depth, shape_name, shape_invalidating_name):
        """
        The saturation process consists of two steps:
        1. Negate: same as in step (1) of procedure ground_and_saturate(...)
        2. Infer: same is step (2) of procedure ground_and_saturate(...)
        Repeat 1 and 2 until no further changes are made (i.e., no new inferences found)

        :param state:
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param shape_name: name of current shape being evaluated
        :param shape_invalidating_name: name of the shape that started the saturation at level 'depth' before recursion
        """
        rule_map = state.shapes_state[shape_name].get_rule_map()
        negated = self.negate_unmatchable_heads(state, depth, rule_map, shape_invalidating_name)
        inferred = self.apply_rules(state, depth, rule_map, shape_invalidating_name)
        if negated or inferred:
            self.saturate_remaining(state, depth, shape_name, shape_invalidating_name)
        else:
            for parent_name in self.shapes_dict[shape_name].getParentShapes():
                state.shapes_state[parent_name].remove_saturated_referenced_shape(shape_name)
                if len(state.shapes_state[parent_name].get_pending_refs_to_saturate()) == 0 \
                   and state.shapes_state[parent_name].get_remaining_targets_count() > 0:
                    self.saturate_remaining(state, depth, parent_name, shape_invalidating_name)

    def eval_constraints_query(self, state, shape, query, best_ref_shape_name, query_rule_pattern, shape_rule_pattern,
                               query_type):
        """
        Evaluates corresponding min/max 'query' of 'shape' and starts interleaving process for each of the answers
        (bindings) retrieved by the query.

        'shape' applies knowledge gained from a referenced shape ('best_ref_shape_name') with already classified targets
        to rewrite 'query' in order to include filtering syntax that contains the targets from 'best_ref_shape_name'.
        Given that the length of a query string is restricted by the endpoint configuration, 'query' might be divided
        into several sub-queries, where each subquery contains at most 'max_inst_per_query' (set to 80) instances.

        :param state:
        :param shape:
        :param query:
        :param best_ref_shape_name:
        :param query_rule_pattern:
        :param shape_rule_pattern:
        :param query_type: string containing "min" or "max"
        :return:
        """
        prev_val_list, prev_inv_list = self.inst_retrieval.get_instances_list(best_ref_shape_name)
        max_split_number = shape.maxSplitSize
        max_inst_per_query = 80

        filtered_query = self.inst_retrieval.filtering_constraint_query(
            shape, query.getSparql(), prev_val_list, prev_inv_list, best_ref_shape_name,
            max_split_number, max_inst_per_query, query_type)

        for queryStr in filtered_query:
            start = time.time() * 1000.0
            for binding in self.inst_retrieval.run_constraint_query(queryStr, query):
                self.ground_and_saturate(binding, state, shape, query_rule_pattern, shape_rule_pattern)
            end = time.time() * 1000.0
            self.stats.recordGroundingTime(end - start)
            self.log_output.write("\nGrounding rules ... \nelapsed: " + str(end - start) + " ms\n")

    def eval_constraints_queries(self, shape, best_ref_shape_name, state):
        """
        Evaluates all constraints queries of 'shape'.
        Skips evaluation of remaining queries if all the targets of a shape were already violated in the
        interleaving (i.e., ground_and_saturate(...)) process

        :param shape:
        :param best_ref_shape_name:
        :param state:
        """
        shape_rule_pattern = shape.getRulePatterns()[0]
        shape_name = shape.getId()

        # There is a single min query per shape (unless split when using filters)
        min_query_rule_pattern = shape.minQuery.getRulePattern()
        self.eval_constraints_query(state, shape, shape.minQuery, best_ref_shape_name,
                                    min_query_rule_pattern, shape_rule_pattern, "min")

        # There might be several max queries per shape
        # Evaluate only if the current shape still has targets to be validated
        if shape_name in self.target_shape_predicates and state.shapes_state[shape_name].get_remaining_targets_count() > 0:
            for q in shape.maxQueries:
                max_query_rule_pattern = q.getRulePattern()
                self.eval_constraints_query(state, shape, q, best_ref_shape_name,
                                            max_query_rule_pattern, shape_rule_pattern, "max")

        # Save rule number
        self.stats.recordNumberOfRules(state.shapes_state[shape_name].get_rule_count())

    def eval_shape(self, state, depth, shape):
        """
        Validates the focus 'shape' by performing a saturation process.

        If all targets corresponding to referenced shapes of 'shape' are already validated, then the focus 'shape'
        starts the evaluation of targets that could not be classified as valid/invalid in the 'interleaving' process.

        :param state:
        :param depth: current level (shape) in the evaluation order / number of shapes evaluated so far
        :param shape: current shape being evaluated
        """
        shape_name = shape.getId()
        self.log_output.write("\nEvaluating queries for shape " + shape_name)

        if shape.hasValidInstances and state.shapes_state[shape_name].get_remaining_targets_count() > 0:
            self.eval_constraints_queries(shape, state.prev_eval_shape_name, state)
            state.evaluated_predicates.update(shape.getPredicates())

            self.log_output.write("\nStarting saturation ...")
            start = time.time() * 1000.0
            if len(state.shapes_state[shape_name].get_pending_refs_to_saturate()) == 0:  # ready to saturate
                self.saturate_remaining(state, depth, shape_name, shape_name)
            end = time.time() * 1000.0

            self.stats.recordSaturationTime(end - start)
            self.log_output.write("\nsaturation ...\nelapsed: " + str(end - start) + " ms")
        else:
            self.log_output.write("\nNo further saturation for shape ..." + shape_name)

        state.add_visited_shape(shape)

        self.log_output.write("\n\nValid targets: " + str(len(state.valid_targets)))
        self.log_output.write("\nInvalid targets: " + str(len(state.invalid_targets)))
        self.log_output.write("\nRemaining targets: " + str(len(state.remaining_targets)))

    @staticmethod
    def get_eval_child_name(shape, visited_shapes):
        """
        Returns the name of a shape that was already evaluated, if it is connected as a child in the network to the
        shape that is currently being validated, and contains relevant information for query filtering purposes, i.e.:
            - the number of valid or invalid instances is less than a threshold (now threshold is set as 256),
            - the list of invalid targets from the child's shape in the network is not empty,
            - there was a target query assigned for this "child" shape (also called "previous evaluated shape").

        :param shape: current shape being evaluated
        :param visited_shapes:
        :return: string with the (best) previously evaluated shape name or None if no shape fulfills the conditions
        """
        best_ref = None
        best_val_threshold = 256
        best_inv_threshold = 256
        for prev_shape in visited_shapes:
            prev_shape_name = prev_shape.getId()
            if shape.referencedShapes.get(prev_shape_name) is not None:
                len_val = len(prev_shape.bindings)
                len_inv = len(prev_shape.invalidBindings)

                if (0 < len_val < best_val_threshold) or (0 < len_inv < best_inv_threshold):
                    if len_inv > 0 and prev_shape.getTargetQuery() is not None:
                        best_ref = prev_shape_name

        return best_ref

    def retrieve_next_targets(self, state, depth, next_focus_shape):
        """
        There are two possible queries for retrieving targets:
           - w/o filtering: retrieve instances belonging to a certain target node (specified in the SHACL file),
           - with filtering: if 'selective queries: true' parameter is enabled, ask for instances that belong to the
                             shape's target nodes and additionally filter retrieving instances based on targets
                             retrieved by an evaluated referenced shape (prev_eval_shape_name).

        :param state:
        :param depth: integer that represents current level in the evaluation order / number of shapes evaluated so far
        :param next_focus_shape: next shape to be validated based on the evaluation order given by 'self.node_order'
        :return:
        """
        self.log_output.write("\n\n****************************************\n********************************")
        self.log_output.write("\nRetrieving (next) targets ...")

        next_focus_shape_name = next_focus_shape.getId()
        state.prev_eval_shape_name = self.get_eval_child_name(next_focus_shape, state.visited_shapes)

        if self.selectivity_enabled and state.prev_eval_shape_name is not None:
                # get instances based on results from evaluated child referenced by the current shape
                pending_targets, inv_targets = self.inst_retrieval.extract_target_atoms_with_filtering(
                    next_focus_shape, self.eval_inst_type, state.prev_eval_shape_name)

                # invalid targets are classified straight away (not considered for further saturation)
                for t in inv_targets:
                    self.register_target(t, False, depth, "negated directly from query", next_focus_shape_name, state)
                    state.shapes_state[next_focus_shape_name].add_inferred_atom(t.getNegation(), False)
                    state.shapes_state[next_focus_shape_name].decrease_remaining_targets_count()
                # valid targets are added to the set of remaining targets
                state.remaining_targets.update(pending_targets)
                state.shapes_state[next_focus_shape_name].set_initial_targets_count(len(pending_targets))
        else:
            pending_targets = self.inst_retrieval.extract_target_atoms(next_focus_shape)
            state.remaining_targets.update(pending_targets)
            state.shapes_state[next_focus_shape_name].set_initial_targets_count(len(pending_targets))

            self.log_output.write("\nNumber of targets: " + str(len(pending_targets)))

    def validate(self, state, depth, focus_shape):
        """
        This procedure performs the following:
        1. Starts remaining saturation of current focus shape (procedure eval_shape(...))
        2. Gets the next shape over which evaluation will be performed.
        3. Retrieves the target instances of the next shape to be evaluated.

        :param state:
        :param depth: integer that represents current level in the evaluation order / number of shapes evaluated so far
        :param focus_shape: current shape being evaluated
        :return:
        """
        # termination condition: all shapes have been visited
        if len(state.visited_shapes) == len(self.shapes_dict):
            if self.eval_inst_type == "valid" or self.eval_inst_type == "all":
                for t in state.remaining_targets:
                    self.register_target(t, True, depth, "not violated after termination", '', state)
            return

        self.log_output.write("\n\n********************************")
        self.log_output.write("\nStarting validation at depth: " + str(depth))

        self.eval_shape(state, depth, focus_shape)  # validate current selected shape

        # select next shape to be evaluated from the already defined list with the evaluation order
        next_focus_shape = None
        if len(self.node_order) > 0:  # if there are more shapes to be evaluated
            next_focus_shape = self.shapes_dict[self.node_order.pop(0)]
            if next_focus_shape.getTargetQuery() is not None:
                self.retrieve_next_targets(state, depth, next_focus_shape)

        self.validate(state, depth + 1, next_focus_shape)


class EvalState:
    def __init__(self, initial_shapes_state, target_literals):
        self.shapes_state = initial_shapes_state
        self.remaining_targets = target_literals
        self.visited_shapes = set()
        self.evaluated_predicates = set()
        self.prev_eval_shape_name = None
        self.valid_targets = set()
        self.invalid_targets = set()
        self.traces = set()
        self.traces_count = 0
        self.valid_targets_after_termination = set()

    def add_visited_shape(self, s):
        self.visited_shapes.add(s)

    def add_valid_target_after_termination(self, t):
        self.valid_targets_after_termination.add(t)

    def get_valid_targets_after_termination(self):
        return self.valid_targets_after_termination
