from TravSHACL.rule_based_validation.Validation import Validation


class ValidationResultStreaming(Validation):

    def __init__(self, endpoint_url, node_order, shapes_dict, target_shape_predicates, use_selective_queries,
                 output_dir_name, save_stats, save_targets_to_file, result_transmitter):
        super().__init__(endpoint_url, node_order, shapes_dict, target_shape_predicates, use_selective_queries,
                         output_dir_name, save_stats, save_targets_to_file)
        self.result_transmitter = result_transmitter

    def exec(self):
        if len(self.node_order) > 0:
            super().exec()
        else:
            self.result_transmitter.done()

    def register_target(self, t, t_type, invalidating_shape_name, shapes_state):
        super().register_target(t, t_type, invalidating_shape_name, shapes_state)
        self.result_transmitter.send(instance=t[1], shape=t[0], valid=(t_type == 'valid'),
                                     reason=invalidating_shape_name)

    def validation_output(self, shapes_state):
        result = super().validation_output(shapes_state)
        for item in self.valid_targets_after_termination:
            self.result_transmitter.send(instance=item[1], shape=item[0], valid=True, reason='unbound')
        self.result_transmitter.done()
        return result
