## Non-equilibrium Thermodynamics ({{areas.Thermodynamics.count}} topics) {#sec:thermodynamics_results}

The thermodynamic interpretation of the FEP draws analogies to statistical mechanics. The {{areas.Thermodynamics.count}} catalogue rows formalize an exact Helmholtz differential identity, finite non-detailed-balance stationary currents, binary maximum entropy and normalized Gibbs weights, discrete fluctuation--response decay, finite entropy-production laws, a conditional Landauer derivation, normalized forward/reverse path laws, detailed and integral fluctuation identities, a finite Jarzynski equality, local-current cancellation, reversible one-step KL dissipation, and an exact two-state continuous-time Markov semigroup with master equation and Lyapunov decay. The motivating continuous-state and physical theories remain broader than these deliberately scoped models.

**Thermodynamics area (current pin).** Every row carries `mathlib_status: real`; semantic dispositions include direct and deliberately proxied scopes and are reported by the generated maturity projection. The receipt-backed native area rate is **`{{compile_rate.by_area.Thermodynamics}}`** when `{{verify.claim_ready}}` is true. Timing is read from that receipt rather than fixed in prose. The area combines calculus, finite sums and matrices, geometric limits, logarithms, exponential weights, native entropy results, finite path-space probability, and one explicit finite-state continuous-time kernel. Its finite and scalar models do not imply continuous-state trajectory theory or continuum statistical mechanics.

### Thermodynamic Free Energy and Partition Structure {#sec:thermo_helmholtz_partition}

For a canonical equilibrium ensemble with the usual definitions of mean energy, entropy, and partition function, the thermodynamic **Helmholtz free energy** takes the equivalent forms:

$$
\mathcal{F} \;=\; U \;-\; T\,S \;=\; -\,k_B\,T\,\log Z, \qquad Z \;=\; \sum_i \exp\!\bigl(-\beta\,E_i\bigr),\; \beta = 1 / (k_B T).
$$ {#eq:thermo_helmholtz}

[@eq:thermo_helmholtz] motivates a formal analogy with variational free energy, but thermodynamic Helmholtz energy does not generically “upper-bound surprise.” The connection requires an explicit choice of energy $E=-k_BT\log p$ and compatible normalization. fep-031 proves positivity and energy monotonicity of exponential weights, positivity of a nonempty finite partition sum, nonnegativity of the normalized weights, and that they sum to one on the selected support. It does not derive the Gibbs form from maximum entropy or construct a thermodynamic ensemble beyond this finite mass function.

### Helmholtz Free Energy Bridge (fep-013): Full Derivation {#sec:thermo_helmholtz_bridge_derivation}

The following calculation states one precise bridge under a fixed observation, common base measure, integrability, and positive temperature. Let $p(s,o)$ be a generative joint density and $q(s)$ a normalized approximate posterior. Define

$$
U_q \;:=\; \mathbb{E}_q\!\bigl[-\log p(s, o)\bigr], \qquad H[q] \;:=\; -\,\mathbb{E}_q\!\bigl[\log q(s)\bigr], \qquad T \;=\; \frac{1}{k_B\,\beta}.
$$ {#eq:thermo_bridge_definitions}

Here $U_q$ is the *internal energy* interpretation of the negative log-joint (each configuration $(s, o)$ is assigned an energy $E(s, o) = -\log p(s, o)$ in natural units), and $H[q]$ is the *Boltzmann entropy* of the posterior $q$. Substituting these definitions into the variational free energy $F_{\text{var}}[q] = \mathbb{E}_q[-\log p(s, o)] - H[q]$ (in nats) yields

$$
F_{\text{var}}[q] \;=\; U_q \;-\; H[q] \;=\; \frac{1}{k_B T}\!\Bigl(\widetilde{U}_q \;-\; T\,\widetilde{S}_q\Bigr),
$$ {#eq:thermo_bridge_nats_to_joules}

where $\widetilde{U}_q = k_B T\,U_q$ and $\widetilde{S}_q = k_B\,H[q]$. Calling the bracketed quantity $\mathcal{F}[q]$ gives the bridge and its Bayesian decomposition:

$$
\boxed{\;F_{\text{var}}[q] \;=\; \frac{\mathcal{F}[q]}{k_B T}
\;=\; D_{\mathrm{KL}}\!\left(q(s)\,\middle\|\,p(s\mid o)\right)-\log p(o)\;}
$$ {#eq:thermo_helmholtz_bridge_exact}

Here the equilibrium free energy is $\mathcal{F}_{\mathrm{eq}}=-k_BT\log p(o)$ and the excess $\mathcal{F}[q]-\mathcal{F}_{\mathrm{eq}}$ is $k_BT$ times the KL divergence. Positive rescaling preserves the argmin:

$$
\mathop{\mathrm{argmin}}_q\,F_{\text{var}}[q] \;=\; \mathop{\mathrm{argmin}}_q\,\mathcal{F}[q].
$$ {#eq:thermo_bridge_argmin_equiv}

Under the stipulated construction and natural scaling, the minimizer is the posterior because the KL term vanishes there. This is a mathematical analogy obtained by defining the energy landscape from the generative density; it is not by itself a physical claim that biological inference is thermodynamic equilibration.

**What fep-013 formalizes.** It defines $F(T)=U(T)-T S(T)$, proves the exact derivative $F'=U'-S-TS'$, and reduces it to $F'=-S$ under the explicit equilibrium first-law identity $U'=TS'$. Boundary, order, and finite-difference laws are retained. The authored `fep013_gaussianHelmholtz_derivative` theorem instantiates this calculus with fep-040's Gaussian thermal entropy and $U(T)=T/2$. The row still does not identify this Helmholtz object with fep-002's variational free energy or prove the density-level bridge in [@eq:thermo_helmholtz_bridge_exact].

### Jarzynski Equality and Fluctuation Theorems {#sec:thermo_jarzynski}

For a system driven by an external protocol that transitions the Hamiltonian from $H_0$ to $H_1$ in finite time, the non-equilibrium work $W$ is a random variable with distribution $P(W)$. The **Jarzynski equality** [@jarzynski1997nonequilibrium] provides an *identity* — not merely an inequality — linking the exponential average of $W$ to the *equilibrium* free energy difference:

$$
\bigl\langle e^{-\beta W} \bigr\rangle \;=\; \int\!P(W)\,e^{-\beta W}\,dW \;=\; e^{-\beta\,\Delta \mathcal{F}}, \qquad \Delta \mathcal{F} = \mathcal{F}_1 - \mathcal{F}_0.
$$ {#eq:thermo_jarzynski}

[@eq:thermo_jarzynski] can hold for protocols driven arbitrarily far from equilibrium, but not without a model: standard derivations assume an initial canonical ensemble and dynamics with the required microscopic reversibility or local-detailed-balance structure, along with a well-defined work functional. Applying Jensen's inequality to [@eq:thermo_jarzynski] recovers the mean-work bound

$$
\langle W \rangle \;\ge\; \Delta \mathcal{F},
$$ {#eq:thermo_second_law_bound}

i.e., the mean work performed is at least the equilibrium free energy difference. Equality requires zero dissipated work almost surely; quasistatic reversible driving is the standard limiting realization. [@eq:thermo_jarzynski] is stronger than [@eq:thermo_second_law_bound]: it fixes an exponential moment of $W$, not merely its mean.

A companion result, the **Crooks fluctuation theorem** [@crooks1999entropy], relates forward and time-reversed work distributions at the level of *individual trajectories*:

$$
\frac{P_F(W)}{P_R(-W)} \;=\; \exp\!\bigl(\beta\,(W - \Delta \mathcal{F})\bigr),
$$ {#eq:thermo_crooks}

where $P_F(W)$ is the probability density of performing work $W$ under the forward protocol (Hamiltonian swept from $H_0$ to $H_1$) and $P_R(-W)$ is the probability density of performing work $-W$ under the time-reversed protocol (swept from $H_1$ to $H_0$). [@eq:thermo_crooks] quantifies the *exponential asymmetry* between a dissipative trajectory and its time-reverse: work excursions above $\Delta \mathcal{F}$ are exponentially more likely in the forward direction, while excursions below $\Delta \mathcal{F}$ are exponentially more likely in reverse. The Jarzynski equality is a direct corollary of Crooks: rearranging [@eq:thermo_crooks] to $P_R(-W) = P_F(W)\,e^{-\beta(W - \Delta\mathcal{F})}$ and integrating $\int P_R(-W)\,dW = 1$ yields [@eq:thermo_jarzynski] immediately.

Both fluctuation identities require trajectory measures and microscopic-reversibility assumptions. fep-010 states detailed balance at Mathlib's measure--Markov-kernel level and proves that reversibility implies invariance; the identity kernel supplies a non-vacuous witness. fep-037 treats a symmetric two-state relaxation and response model. The path-space expansion then constructs normalized finite forward and reversed path laws, proves involutive reversal and full-support ratios, defines entropy production as finite KL, and derives detailed and integral fluctuation identities. fep-097 proves a finite Jarzynski equality from an explicit inverse temperature, work functional, free-energy difference, and pointwise exponential normalization. These are exact finite path-law identities. They do not establish the continuous work-density Crooks theorem in [@eq:thermo_crooks] without the corresponding pushforward and protocol structure.

### NESS Solenoidal Flow (fep-025): Target Fokker–Planck Structure {#sec:thermo_ness_fokker_planck}

The Fokker–Planck equation describes the time evolution of the probability density $p(x, t)$ of a stochastic process $\dot{x} = f(x) + \sqrt{2D}\,\xi(t)$ with drift $f$ and diffusion $D$:

$$
\frac{\partial p(x, t)}{\partial t} \;=\; -\nabla \cdot J(x, t), \qquad J(x, t) \;=\; f(x)\,p(x, t) \;-\; D\,\nabla p(x, t).
$$ {#eq:thermo_fokker_planck}

The vector $J(x, t)$ is the **probability current**: the net flux of probability mass through a point. At a stationary distribution $p^*(x)$ with $\partial_t p^* = 0$, [@eq:thermo_fokker_planck] reduces to the continuity constraint

$$
\nabla \cdot J^*(x) \;=\; 0 \qquad \text{(stationarity)}.
$$ {#eq:thermo_stationarity}

Under the regular constant-diffusion model written above, two important stationary cases are:

1. **Zero-current equilibrium:** $J^*(x) \equiv 0$. With the additional reversibility assumptions connecting the diffusion to its stationary law, this is the detailed-balance case.
2. **Nonequilibrium steady state (NESS):** $J^*(x) \not\equiv 0$ but $\nabla \cdot J^*(x) = 0$. A nonzero stationary current breaks zero-current detailed balance; positive thermodynamic entropy production requires further constitutive and time-reversal structure.

NESS models are often used when describing driven, dissipative biological systems, but that application is a modeling choice rather than a consequence of stationarity alone. In one simplified constant-diffusion ansatz, a drift is written using a **Helmholtz–Ao-type decomposition** [@ao2004potential]:

$$
f(x) \;=\; -\,\bigl(D \,+\, Q(x)\bigr)\,\nabla F(x), \qquad F(x) \;=\; -\log p^*(x), \qquad Q(x)^\top \;=\; -\,Q(x),
$$ {#eq:thermo_ao_decomposition}

where $F(x)$ is the negative log-stationary density up to normalization, $D$ is symmetric positive-semidefinite, and $Q(x)$ is antisymmetric. Within this ansatz, substituting $p^*\propto e^{-F}$ into the current cancels the two $D$ terms and leaves $J^*=-Q\,\nabla F\,p^*$. This algebra does not show that an arbitrary drift admits the ansatz, that the density exists, or that the remaining current is divergence-free; state-dependent diffusion conventions can also introduce additional terms.

**What antisymmetry cancels.** Expanding the candidate current's divergence shows which terms vanish algebraically and which require an additional hypothesis:

$$
\frac{1}{p^*}\,\nabla \cdot \bigl(Q\,\nabla F\,p^*\bigr) \;=\; \mathrm{tr}\!\bigl(Q \cdot \nabla^2 F\bigr) \;-\; \bigl(\nabla F\bigr)^\top\,Q\,\bigl(\nabla F\bigr) \;+\; \bigl(\nabla \cdot Q\bigr)^\top \nabla F.
$$ {#eq:thermo_solenoidal_divergence}

The trace term vanishes when $F$ is sufficiently smooth because $Q$ is antisymmetric and the Hessian is symmetric. The quadratic term also vanishes because an antisymmetric bilinear form is zero on a repeated vector. The remaining $(\nabla\cdot Q)^\top\nabla F$ term does not vanish from antisymmetry alone; it needs, for example, spatially constant $Q$ or a separate orthogonality condition. Thus even this restricted ansatz requires an explicit divergence check. It does not imply that removing $Q$ forces every stochastic system to detailed-balance equilibrium.

**What fep-025 formalizes.** It defines a finite edge current $J_{ij}=\pi_iP_{ij}-\pi_jP_{ji}$ and its node divergence. Lean proves antisymmetry, zero self-current, global conservation, and the pointwise zero-divergence consequence of row normalization and stationarity. A directed three-state cycle then proves existence of a nonzero divergence-free stationary current, formally separating stationarity from detailed balance. This is a finite NESS witness. It does not formalize the trace cancellation, a Hessian, a state-dependent $Q$, or any PDE/SDE in [@eq:thermo_solenoidal_divergence].

### Maximum Entropy (fep-030): Jaynes' Derivation {#sec:thermo_max_entropy_jaynes}

Jaynes' **maximum-entropy principle** [@jaynes1957information] provides a constructive answer to the question "*given that I know only the expectation values $\langle f_i \rangle = c_i$ of certain observables, which probability distribution should I assign?*" The principle says: assign the distribution $p^*$ that maximizes the Shannon/Boltzmann entropy $H[p] = -\mathbb{E}_p[\log p]$ subject to the constraints, and no others. This is the least-biased inference consistent with the data: any other distribution would implicitly assume information the data did not provide.

The constrained-optimization problem is

$$
p^* \;=\; \mathop{\mathrm{argmax}}_{p}\,H[p] \quad \text{subject to}\quad \sum_x p(x) = 1,\;\; \sum_x p(x)\,f_i(x) = c_i \; (i = 1, \dots, k).
$$ {#eq:thermo_maxent_problem}

For a finite feasible problem whose optimum lies in the positive interior and satisfies the relevant constraint qualification, introducing Lagrange multipliers $\lambda_0$ for normalization and $\lambda_i$ for each constraint yields the stationarity condition $-\log p^*(x) - 1 - \lambda_0 - \sum_i \lambda_i f_i(x) = 0$. The resulting candidate has **Boltzmann–Gibbs form**:

$$
p^*(x) \;=\; \frac{1}{Z(\lambda)}\,\exp\!\Bigl(-\!\sum_{i=1}^{k} \lambda_i\,f_i(x)\Bigr), \qquad Z(\lambda) \;=\; \sum_x \exp\!\Bigl(-\!\sum_{i=1}^{k} \lambda_i\,f_i(x)\Bigr).
$$ {#eq:thermo_maxent_gibbs_form}

When a matching multiplier exists, enforcing the constraints relates derivatives of the log partition function to the prescribed moments. This is the familiar maximum-entropy route to exponential families, subject to feasibility, support, boundary, and dual-attainment qualifications. fep-030 and fep-031 do not prove that general optimization-to-Gibbs bridge. They compose at one exact boundary: for a two-state Gibbs law at zero inverse temperature, hence the infinite-temperature limit, `FEPComposed.fep031_zeroBeta_binary_maxEntropy` rewrites the selected probability to $1/2$ and invokes fep-030's binary-entropy equality characterization. The separate fep-142--148 family constructs a full-support finite scalar exponential family and proves log-partition, Fisher--variance, and KL--Bregman identities, but it assumes the family rather than deriving it as the solution of [@eq:thermo_maxent_problem]. Here $\beta=0$ must not be described as zero physical temperature.

**Two canonical special cases.** (i) *Uniform distribution:* with no constraints beyond normalization, the maximizer is $p^*(x) = 1/n$ on a finite set of size $n$, achieving $H[p^*] = \log n$. This is the classical "principle of insufficient reason". (ii) *Canonical ensemble:* with the single constraint $\langle E \rangle = \bar{E}$, the maximizer is $p^*(x) \propto \exp(-\beta E(x))$ with $\beta = \lambda_1$ identified as inverse temperature.

**What fep-030 formalizes.** It imports Mathlib's binary entropy, proves the global bound $\operatorname{binEntropy}(p)\le\log 2$, and proves equality exactly at $p=1/2$. It also retains the explicit finite-uniform normalization and entropy-equals-$\log n$ calculation. The binary theorem is a genuine maximum-entropy result; the arbitrary finite-simplex and constrained Jaynes problems remain unproved. The composed zero-inverse-temperature theorem connects the binary Gibbs special case to this maximum, but it does not derive general Gibbs weights from constrained optimization.

### Entropy Production and the Variational–Thermodynamic Bridge {#sec:thermo_entropy_production_bridge}

In a one-flux/one-force schematic, a local **entropy-production contribution** is often written as the pairing of a thermodynamic flux $J$ with a conjugate force $F$; sign, mobility, integration, and time-reversal conventions are model-dependent:

$$
\sigma \;=\; J \cdot F \;=\; \mathbf{J} \cdot \nabla \log p \;\ge\; 0,
$$ {#eq:thermo_entropy_production}

The conditions for nonnegativity and equality depend on the constitutive relation and inner product; nonzero flux alone does not imply a positive scalar product with force. [@eq:thermo_entropy_production] is motivating thermodynamics, not a consequence of scalar sign assumptions alone.

Topic **fep-049** formalizes two finite constitutive models. For diagonal linear response $J_i=L_iX_i$, entropy production is the quadratic form $\sum_i L_iX_i^2$; Lean proves nonnegativity for $L_i\ge0$ and zero iff all forces vanish for $L_i>0$. Independently, strictly positive forward/reverse edge fluxes have production $(f-r)\log(f/r)\ge0$, with equality exactly at detailed balance $f=r$. These are genuine finite second-law instances under explicit constitutive assumptions, not a microscopic derivation or a theorem for arbitrary cross-coupled Onsager matrices.

The bridge calculation above becomes exact only after a generative density is used to define an energy landscape and units are fixed. The present Lean rows do connect selected thermodynamic interfaces: fep-025 currents feed fep-049's nonnegative diagonal dissipation, and fep-040 thermal entropy feeds fep-013's Helmholtz derivative. They still do not identify biological self-organization with physical relaxation, because no theorem maps a concrete generative model, stationary law, thermodynamic force, and variational objective into one shared dynamics.

### Landauer Bound (fep-050): Information–Thermodynamic Interpretation {#sec:thermo_landauer}

**Landauer's principle** [@landauer1961irreversibility] asserts that erasing one bit of information from a physical memory has an irreducible thermodynamic cost of at least

$$
W_{\text{erase}} \;\ge\; k_B\,T\,\log 2 \;\approx\; 2.9 \times 10^{-21}\,\text{J at }T=300\,\text{K}.
$$ {#eq:thermo_landauer_bound}

In the standard idealized symmetric-memory model, an initially equiprobable bit has Shannon entropy $\log 2$ nats and a reset state has zero logical entropy. A cyclic isothermal implementation must compensate that entropy decrease in the environment; in the reversible limit this gives the $k_BT\log2$ minimum. More general Landauer results are formulated through nonequilibrium free-energy changes and depend on the physical memory, control protocol, reservoir, and error tolerance. The bound is therefore not obtained from information entropy plus the first law without those modeling assumptions.

Landauer's bound applies to logically irreversible erasure under physical assumptions; it is not a cost per Bayesian update, per bit observed, or per nat of KL reduction. Deriving a neural-metabolic rate limit would require an explicit physical implementation, a count of irreversible erasures, temperature/control assumptions, and a link from algorithmic state changes to thermodynamic operations. Neither the general principle nor fep-050 supplies that bridge.

**What fep-050 formalizes.** It defines a noninjective Boolean reset, computes the entropy lost by erasing an unbiased bit as $k_B\log2$, and models environmental entropy change as $Q/T$. From positive temperature and the explicit second-law hypothesis $\Delta S_{\mathrm{total}}\ge0$, Lean derives $Q\ge k_BT\log2$; a separate work-at-least-heat hypothesis yields the work bound. Thus the thermodynamic inference is explicit and checkable, while the second law and implementation energetics remain assumptions rather than a microscopic Hamiltonian derivation.

### Lean 4 Formalization: Entropy, Boltzmann, and Landauer {#sec:thermo_lean_sketches}

The thermodynamic topics encode six distinct, composable layers of the theory:

- **Binary maximum entropy plus uniform calculation (fep-030)** — native `Real.binEntropy` is bounded by $\log 2$ with equality exactly at $1/2$; uniform finite weights are separately normalized and their entropy expression equals $\log n$. General finite-simplex maximality is not proved.
- **Finite Boltzmann--Gibbs weights (fep-031)** — Exponential-weight positivity, energy-ordered monotonicity at positive inverse temperature, partition-sum positivity, pointwise nonnegativity after normalization, and exact mass one on a nonempty selected support.
- **Differential Helmholtz law (fep-013)** — $F=U-TS$ is differentiated exactly, and the equilibrium first-law premise reduces $F'$ to $-S$; fep-040 supplies a concrete Gaussian thermal instance.
- **Stationarity, response, and production (fep-025, fep-037, fep-049)** — finite nonzero stationary currents, exact two-state response decay, quadratic entropy production, and edge detailed-balance separation are theorem-level objects.
- **Conditional Landauer derivation (fep-050)** — erasure entropy loss plus an explicit second-law premise derives the heat bound, and work-at-least-heat derives the work bound.
- **Finite path thermodynamics (fep-093--099)** — normalized forward/reverse path laws, involutive reversal, path-ratio and fluctuation identities, finite Jarzynski normalization, local current cancellation, and reversible KL dissipation with explicit irreversible and zero-rate boundaries.
- **Two-state continuous time (fep-149--155)** — a positive-rate Boolean Markov kernel, identity and Chapman--Kolmogorov laws, left and right master equations, a nonuniform detailed-balance stationary law, exact exponential relaxation, and quadratic Lyapunov decay with a strict nonstationary benchmark.

| Topic | Actual Lean content | Semantic disposition | Modules imported (`Mathlib.` prefix omitted) | `sorry` count |
|-------|---------|----------|--------------------------|--------|
| fep-013 | Helmholtz definition, exact derivative, and equilibrium reduction to $-S$ | `{{topics.fep-013.semantic_disposition}}` | {{topics.fep-013.imported_modules}} | 0 |
| fep-025 | Finite probability current, conservation, stationarity, and nonzero three-cycle witness | `{{topics.fep-025.semantic_disposition}}` | {{topics.fep-025.imported_modules}} | 0 |
| fep-030 | Native binary-entropy maximum/equality characterization and exact uniform finite entropy | `{{topics.fep-030.semantic_disposition}}` | {{topics.fep-030.imported_modules}} | 0 |
| fep-031 | Finite Gibbs-weight positivity, energy monotonicity, normalization, and mass one | `{{topics.fep-031.semantic_disposition}}` | {{topics.fep-031.imported_modules}} | 0 |
| fep-037 | Two-state autocorrelation recurrence/decay and exact fluctuation--response kernel | `{{topics.fep-037.semantic_disposition}}` | {{topics.fep-037.imported_modules}} | 0 |
| fep-049 | Finite quadratic and edge-flux entropy production with equilibrium separation | `{{topics.fep-049.semantic_disposition}}` | {{topics.fep-049.imported_modules}} | 0 |
| fep-050 | Boolean erasure entropy loss and conditional Landauer heat/work derivation | `{{topics.fep-050.semantic_disposition}}` | {{topics.fep-050.imported_modules}} | 0 |
| fep-093 | Normalized finite forward/reverse path laws, reversal, and full-support ratio | `{{topics.fep-093.semantic_disposition}}` | {{topics.fep-093.imported_modules}} | 0 |
| fep-094 | Finite path entropy production identified with finite KL | `{{topics.fep-094.semantic_disposition}}` | {{topics.fep-094.imported_modules}} | 0 |
| fep-095 | Detailed finite fluctuation symmetry from the path-law ratio | `{{topics.fep-095.semantic_disposition}}` | {{topics.fep-095.imported_modules}} | 0 |
| fep-096 | Integral fluctuation identity under normalized full-support path laws | `{{topics.fep-096.semantic_disposition}}` | {{topics.fep-096.imported_modules}} | 0 |
| fep-097 | Finite Jarzynski identity with explicit work, inverse temperature, and normalization | `{{topics.fep-097.semantic_disposition}}` | {{topics.fep-097.imported_modules}} | 0 |
| fep-098 | Local detailed balance and edge-current cancellation | `{{topics.fep-098.semantic_disposition}}` | {{topics.fep-098.imported_modules}} | 0 |
| fep-099 | Reversible one-step KL dissipation and irreversible positive-production witness | `{{topics.fep-099.semantic_disposition}}` | {{topics.fep-099.imported_modules}} | 0 |
| fep-149 | Positive-rate two-state continuous-time Markov kernel and nonuniform benchmark | `{{topics.fep-149.semantic_disposition}}` | {{topics.fep-149.imported_modules}} | 0 |
| fep-150 | Continuous-time transition is the identity at time zero | `{{topics.fep-150.semantic_disposition}}` | {{topics.fep-150.imported_modules}} | 0 |
| fep-151 | Exact Chapman--Kolmogorov semigroup law | `{{topics.fep-151.semantic_disposition}}` | {{topics.fep-151.imported_modules}} | 0 |
| fep-152 | Entrywise left and right continuous-time master equations | `{{topics.fep-152.semantic_disposition}}` | {{topics.fep-152.imported_modules}} | 0 |
| fep-153 | Stationarity and detailed balance for the exact semigroup | `{{topics.fep-153.semantic_disposition}}` | {{topics.fep-153.imported_modules}} | 0 |
| fep-154 | Exact exponential relaxation from an arbitrary normalized Boolean law | `{{topics.fep-154.semantic_disposition}}` | {{topics.fep-154.imported_modules}} | 0 |
| fep-155 | Exact quadratic Lyapunov law, derivative, and strict benchmark decay | `{{topics.fep-155.semantic_disposition}}` | {{topics.fep-155.imported_modules}} | 0 |
: Thermodynamics topics: the Lean content each row actually states, its semantic disposition, the modules its Lean body imports (generated from the body, `Mathlib.` omitted), and its `sorry` count.

The strongest direct facts form a chain rather than an isolated roster: fep-030 and fep-031 meet at the binary infinite-temperature maximum; fep-025's finite currents feed fep-049's dissipation law; fep-040's Gaussian thermal entropy feeds fep-013's Helmholtz derivative; and fep-050 derives Landauer heat and work bounds from named physical premises. Each chain is narrower than the full physical theory, but each seam is checked in Lean.

**Key formalization — Helmholtz free energy $F = U - TS$ (fep-013)**: The row represents temperature-dependent internal energy and entropy as differentiable real functions, proves the product-rule derivative $U'-S-TS'$, and derives $F'=-S$ from $U'=TS'$. Boundary and monotonicity laws remain available. The separate fep-040 composition supplies a Gaussian thermal witness; no theorem identifies thermodynamic and variational free energy.

**Mathlib4 module footprint (Thermodynamics)**: The area routes through `Analysis.SpecialFunctions.BinaryEntropy`, real differentiation, geometric-limit results, logarithms and exponentials, finite big operators, and matrix notation. The generated coverage report, rather than this illustrative roster, is the exact import authority.

**Thermodynamic vs variational free energy — formally distinct Lean objects**: The thermodynamic object fep-013 consumes $U(T)$, $T$, and $S(T)$, whereas fep-002 defines variational free energy as surprisal plus native measure KL. Their types and assumptions are deliberately distinct. The Gaussian composition closes one thermodynamic instance, and the fep-002/fep-014 composition closes the KL chain rule, but no theorem identifies these two free energies. Such a theorem would need a concrete density, energy map, units, normalization, and integrability contract.

**Representative formalization** — *Helmholtz differential identity (fep-013)*: The row proves the exact derivative law and its equilibrium reduction under explicit differentiability and first-law assumptions. The composition with fep-040 supplies a nontrivial entropy function rather than an arbitrary scalar witness. It does not derive the first law or the physical meaning of temperature. See [@sec:catalogue-fep-013] in Appendix B and [@sec:eqs-fep-013] in [@sec:appendix_c_latex_equations].

**Representative formalization** — *Finite stationary probability current (fep-025, [@eq:eq_25])*: Some NESS constructions posit a Helmholtz/Ao decomposition [@ao2004potential] with a skew component:

$$
\dot\rho = -\nabla \cdot \bigl(\rho\,\nabla \FE + Q\rho\bigr) = 0, \qquad Q = -Q^\top
$$ {#eq:eq_25}

The row proves the finite continuity analogue directly: a stationary normalized transition has zero current divergence, and a directed three-cycle has both zero divergence and nonzero current. Antisymmetry alone still does not discharge the state-dependent continuum term, and the row has no Hessian or PDE. See [@sec:catalogue-fep-025] in Appendix B and [@sec:eqs-fep-025] in [@sec:appendix_c_latex_equations].

**Representative formalization** — *Conditional Landauer derivation (fep-050)*: The row proves the reset is noninjective, computes unbiased-bit entropy loss, derives the heat bound from total-entropy nonnegativity, and derives the work bound from work-at-least-heat. The physical premises are visible theorem hypotheses rather than hidden in prose.

### Closing Synthesis: What the Thermodynamics Theorems Establish {#sec:thermo_synthesis}

The {{areas.Thermodynamics.count}} rows form a finite, executable thermodynamic layer:

- **Free energy and finite ensembles.** fep-013 proves Helmholtz calculus; fep-030 proves the binary entropy maximum; fep-031 normalizes finite Gibbs weights; composed theorems connect the Gaussian and binary special cases.
- **Stationarity and response.** fep-010 proves reversible-kernel invariance; fep-025 constructs a nonzero divergence-free finite current; fep-037 proves exact discrete two-state correlation and response decay; and fep-149--155 prove an exact two-state continuous-time semigroup, master equation, detailed balance, relaxation, and Lyapunov decay.
- **Production and erasure.** fep-049 proves finite quadratic and edge-flux production laws with equality characterizations; fep-050 derives Landauer heat and work bounds from explicit second-law and work-transfer premises.
- **Path thermodynamics.** fep-093--099 construct finite path laws, entropy production, detailed/integral fluctuation and Jarzynski identities, local detailed-balance currents, and reversible KL dissipation on the shared finite Markov carrier.

The remaining theorems are substantive: the measure-theoretic Helmholtz/variational bridge, a general constrained maximum-entropy derivation of Gibbs laws, continuous or singular path measures, the full protocol-level Crooks work-distribution theorem, generic CTMC construction, continuous-state NESS existence, cross-coupled constitutive response, and a microscopic finite-time erasure model. A fresh warning-free exact-roster receipt would establish acceptance of the present finite mathematics at the pinned toolchain; even then, it would remain a scoped thermodynamic formalization layer rather than a universal physical derivation of the FEP.
