# Issue75 independent semantic review: geometric-mechanics-notation

Exact EF source epoch; family roster verified. 7 rows reviewed. Static family coverage now168/168, without broad acceptance. Current dispositions retained for exact statements; listed metadata corrections remain required.

## fep-161: Skew Bilinear Cancellation of the Trace and Quadratic Terms

Primary `fep161_skewTrace_eq_zero`; current `formalized` retained for exact narrowed statement.

Trace(QH)=0 for plain skew Q and symmetric H, and g-transpose Q g=0 for skew Q. Pairwise summation proves exact finite real identities.

No actual derivatives/Hessian or smooth fields are inputs. Fin n includes0/1 where skew may only be0; nonzero examples require dimension>=2. Plain skew is distinct from160 law-weighted skew.

160 reexports the same algebra;161 isolates its precise unweighted hypotheses. The argument does not prove a solenoidal vector field has zero divergence.

UNEXECUTED positive specification: Q[[0,1],[-1,0]],Hdiag(1,2),g(1,1): trace and quadratic cancellations with nonzero data.

UNEXECUTED adverse specification: A nonskew Q or nonsymmetric H can give nonzero contraction; for H=Q with nonzero2D skew, trace(QH)=-2.

## fep-162: The Discrete Hessian as a Symmetrization Construction

Primary `fep162_skewTrace_symmetrize_eq_zero`; current `formalized` retained for exact narrowed statement.

symmetrize(H)=(H+H-transpose)/2 is symmetric by construction; skew trace cancellation applies to that matrix, and symmetrization fixes every already symmetric H.

This is a finite matrix projection, not Clairaut commutation for an actual twice-differentiable function or consistency of mixed-difference quotients. Replacing data by symmetric data may change it;167 quantifies the residual.

161 consumes symmetric H;162 constructs one;167 later proves actual Frobenius optimality/uniqueness of this construction.

UNEXECUTED positive specification: Raw H[[0,1],[0,0]] becomes[[0,1/2],[1/2,0]] with a nonzero change; symmetric H is unchanged.

UNEXECUTED adverse specification: An actual nonsymmetric derivative-data matrix is not proved to be a Hessian by averaging it. Any identification with second derivatives needs smoothness and correct mixed-index orientation.

## fep-163: The Three-Term Solenoidal Expansion and Its Conditional Drop

Primary `fep163_solenoidal_expansion`; current `formalized` retained for exact narrowed statement.

Explicit Q,H,DQ,g,dlogp data define weighted divergence through a Leibniz sum. Under dlogp=-g it is trace(QH)-g-transposeQg+divQ(DQ) dot g. Skew Q and symmetric H remove first two terms; orthogonality or DQ0 removes the remainder. A derivative-data witness has remainder1.

H(l,k) denotes supplied partial_k g_l; DQ(k,l) supplied partial_k Q_kl. The weightedDivergence is defined algebraically rather than proved equal to analytic divergence of a field. H symmetry/coupling/DQ0 are explicit hypotheses, not consequences of stationarity alone. Existing outside-S current bridge is a proposal, not integrated source.

161 cancellations feed163;164 graph divergence gives a distinct exact finite law. A continuum/current relation requires an actual derivative/codomain bridge.

UNEXECUTED positive specification: Use actual expansion_remainder_witness and skew/symmetric/coupled data to retain remainder1; use DQ0 for a valid conditional drop.

UNEXECUTED adverse specification: Skew Q plus symmetric H and coupling alone do not force divQ(DQ) dot g0. Graph nodeDiv is a separate carrier and cannot be substituted for these directional derivative slots.

## fep-164: Graph Divergence of the Candidate Solenoidal Current

Primary `fep164_graphDecomposition`; current `formalized` retained for exact narrowed statement.

On directed edge matrices with outflow-minus-inflow node divergence, skew Q gives nodeDiv Q=2rowSum Q. For currentOf(Q,g)(i,j)=Qij*g_j its node divergence is Qg_i+g_i*rowSum_i. Positive node weights yield an exact additional weighted residual.

This is graph algebra, not an analytic divergence discretization theorem. Positive density need not normalize; currentOf is an edge field whereas mulVec Qg is a node vector. Residual can vanish on special data and is not forced nonzero solely by nodeDiv_skew.

025 earlier current/divergence conservation and163 derivative data use different contractions.164 proves exact graph identities retaining the density residual.

UNEXECUTED positive specification: Use165 skewQ and g(1,0): edge-current node divergence(1,-1) while mulVecQg=(0,-1). Nonuniform positive p exercises weighted residual.

UNEXECUTED adverse specification: A balanced skew cycle may have rowSum0, so skewness does not force a nonzero row sum. Constant g or special densities can cancel terms; no universal residual sign follows.

## fep-165: Necessity Witness for the Unconditional Solenoidal Drop

Primary `fep165_witness_drop_fails`; current `formalized` retained for exact narrowed statement.

The explicit2-node skew Q and node vector g produce mulVecQg=(0,-1), nodeDivQ=(2,-2), and nodeDiv(currentOf Q g)=(1,-1), so graph-current divergence is nonzero at node0.

This is a graph counterexample. It supplies no H,DQ,dlogp and therefore cannot establish failure of163 orthogonality or DQ0 hypotheses. A spatially constant skew matrix can have DQ0 in the derivative-data plane yet nonzero graph row divergence. The actual163 remainder witness separately refutes dropping a nonzero derivative-data remainder.

163 pointwise/derivative-data drop and165 graph drop are distinct. Retain formalized for the graph witness, but correct the metadata claim about unavailable163 hypotheses.

UNEXECUTED positive specification: Reuse all five exact graph witness declarations, carefully distinguishing node current from edge field.

UNEXECUTED adverse specification: Set the same Q,g with H0,DQ0,dlogp=-g in163: its weightedDivergence is0 while the graph node divergence is1. Thus these are not interchangeable countermodels.

## fep-167: Frobenius Least-Squares Projection of the Symmetrizer

Primary `fep167_frobenius_pythagoras`; current `formalized` retained for exact narrowed statement.

Frobenius Pythagoras decomposes squared distance to any symmetric S into symmetrization residual plus symmetric projection distance. This proves minimizing symmetrizer, equality iff S=symmetrizeH and unique symmetric minimum. Explicit nonsymmetric datum has residual1/2.

This is actual constructed finite matrix least-squares optimality, stronger than merely assuming a projection certificate. It does not establish differentiability/Clairaut or arbitrary Bregman projection properties.

162 constructs symmetry and105 assumes abstract Bregman projection;167 gives a concrete Euclidean/Frobenius projection proof without solving general105 existence.

UNEXECUTED positive specification: Use raw[[0,1],[0,0]] and its symmetric average; verify residual1/2 and uniqueness. Symmetric raw data has residual0.

UNEXECUTED adverse specification: A nonsymmetric competitor H itself can have distance0 but is outside the symmetric feasible set. Different weighted norms require a new projection formula/proof.

## fep-168: Quantitative Control of the Uncancelled Divergence Remainder

Primary `fep168_weightedDivergence_eq_remainderDot`; current `formalized` retained for exact narrowed statement.

Under skew Q,symmetric H and dlogp=-g, weightedDivergence equals the explicit remainder r dot g. Finite Cauchy–Schwarz bounds its square by(r dot r)*(g dot g); abs-product version is equivalent and aligned nonzero data attain equality.

This budget controls algebraic derivative data, not physical entropy production, PDE discretization error or probabilistic failure. Coupling is sufficient, not necessary; other data can also make the coupling slot cancel. No smallness follows unless actual remainder/gradient norms are bounded.

163 qualitative uncancelled remainder becomes a quantitative exact norm budget;165 graph counterexample is separate and cannot supply these derivative norms without a bridge.

UNEXECUTED positive specification: Use the actual aligned g(1,0),r(1,0),Hdiag(1,2): equality with nonzero norm; r(1,0),g(1,1) gives strict gap1.

UNEXECUTED adverse specification: Large DQ scales the remainder arbitrarily while skew/symmetric conditions persist. An unbounded remainder cannot be dropped because a Cauchy–Schwarz inequality exists.

## Exact field corrections

### P2 fep-165 / invariant

Graph counterexample does not establish failure of163 derivative-data orthogonality or DQ=0 hypotheses.

Complete replacement field text: For the exact two-node skew transport matrix[[0,1],[-1,0]] and gradient(1,0), the node vector Qg is(0,-1), graph node divergence of Q is(2,-2), and graph node divergence of currentOf(Q,g) is(1,-1), hence1 at node0. This refutes an unconditional zero graph-current-divergence claim. No H,DQ or dlogp data are supplied here; the separate fep-163 remainder witness addresses its derivative-data carrier.

### P2 fep-165 / assumption_review

The graph and derivative-data planes are not interchangeable exact hypothesis classes.

Complete replacement field text: This is a concrete finite graph counterexample with outflow-minus-inflow node divergence and edge current Qij*g_j. It does not assert that fep-163 orthogonality or spatially constant-Q directional-derivative hypotheses fail: those involve separately supplied DQ data. Identifying graph divergence with analytic or fep-163 weighted derivative divergence would require a separate proved bridge.

### P2 fep-165 / non_vacuity

Refutation must name the graph hypothesis class.

Complete replacement field text: The exact graph witness evaluates nodeDiv(currentOf Q g) at node0 to1 despite plain skew Q. It is nonvacuous for that graph claim. On the derivative-data carrier, the same pointwise Q and g can instead be paired with H=0,DQ=0,dlogp=-g and have weightedDivergence=0; the two divergence notions are not identified.

## Ranked bounded follow-ups

1. 165 exact graph-versus-derivative boundary: Apply exact metadata correction distinguishing graph counterexample and163 directional-data theorem. Existing graph witness remains valid; no source proof change required. Estimate: 0.5–1 day with metadata seals/projections.

2. 163 actual analytic derivative bridge: A true analytic divergence identification requires differentiable Q(x),g(x),positive density and explicit product/chain rules with H(l,k)=partial_k g_l. Existing outside-repository current-bridge proposal must be reviewed/integrated separately; no PDE existence follows. Estimate: 2–5 day bounded finite-dimensional API spike.

3. 167/168 quantitative actual consumers: Reuse exact Frobenius minimizer and Cauchy–Schwarz equality/strict witnesses; any numerical/PDE error budget requires actual norm bounds and carrier/codomain identification. Estimate: 0.5–1.5 days typed consumers.

## Bindings and limits

Adjacent JSON binds all exact declaration statements, complete maturity/novelty records, touching relations, canonical body hashes and source-file SHA256 values. All168 rows now have static family audits; metadata corrections, dependency acceptance, independent evidence renewal and integration/publication remain open. No empirical, full scientific or terminal human acceptance is inferred.
