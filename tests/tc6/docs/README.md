# Test Case TC6

TC6 is different from the other test cases in the sense that it is not used to check the correctness of the validation result.
In TC6 the constraint removal feature is tested; also in the case of removing constraints from an OR constraint.

TC6 consists of two shapes. `ShapeA` comprises three constraints.
One of the constraints is an OR constraint including three constraints.
One of the remaining constraints links `ShapeA` to `ShapeB`.
`ShapeB` has no constraints and is only used to check whether a shape is removed from the schema if it is not reachable in the reduced network.

The covered cases are:
- Remove one of the constraints from the OR constraint
- Remove two of the constraints from the OR constraint; should result in two regular constraints
- Remove all constraints from the OR constraint; should result in a single constraint (the remaining one)
- Remove all constraints but one from the OR constraint; should result in a single constraint which was previously part of the OR constraint

Additionally, it is checked whether `ShapeB` is removed from the shape schema if the constraint linking the shapes is removed.
Inverse paths are also covered as one of the constraints of the OR constraint uses an inverse path and is removed in two of the four tests.