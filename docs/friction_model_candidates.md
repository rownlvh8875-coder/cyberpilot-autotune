# Preregistered candidate families

| Family | Equation / recovery | Required state / caveat |
|---|---|---|
| Controller | u=a/F+Cq+b0; F=1/beta_a, C=beta_q | raw pre-PID callback output, exact callback a and q; rank[a,q,1]=3 |
| Inverse | a=F*u-F*C*q+b; C=-beta_q/beta_u | same states, rank[u,q,1]=3; torque regressor EIV |
| Branch | a=F*u+b±, b_minus-b_plus=2FC | saturated q=±1, within-branch variation; unequal occupancy retained, asymmetry diagnosed |
| Explicit | h=Cq+b_h | independent h if scientific; constructed h/current C only code-consistency |

The inverse regression coefficient on q is **negative F*C**. A positive
symbol beta_2=F*C is permissible only in an equation written with
`-beta_2*q`; never divide the signed fitted coefficient without negation.

All four are deterministic offline synthetic prototypes, not runtime
estimators. Known F, jointly unknown F, and F-interval sensitivity are separate
experiments. Compare structural identifiability, required signals, F dependence,
noise sensitivity, closed-loop bias, excitation, mode compatibility, complexity,
source grounding, route feasibility and upstream friendliness. Selection rules
are fixed in friction_model_policy.json before results.

PID alternatives are raw feedforward, low-error steady subset, explicit
PID subtraction, and a joint dynamic model. Only the first is directly the
linear callback estimand; no selected real steady threshold exists, subtraction
cannot undo clipping/actuator limits, and no physical dynamic model is qualified.
LINEAR-only conditional recovery must not silently include NN/GM/custom modes.

Geometry tests use the exact coherent stiffness redistribution, both steady
curvature/roll and a dynamic bicycle transient. No presumption that steady
curvature must change: algebra may cancel ratio dependence. A missing or
changed geometry cohort rejects pooling even in a numerically invariant case.
