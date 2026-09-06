## Sophisticated Dynamics: Information Geometry and Bayesian Mechanics {#sec:sophisticated_dynamics_information_geometry_and_bayesian_mechanics}

Two catalogue areas target especially demanding mathematics: **Information Geometry ({{areas.InfoGeometry.count}} topics)** and **Bayesian Mechanics ({{areas.BayesianMechanics.count}} topics)**—together {{combined_info_bayes_count}} of the {{total_topics}} bodies. Their motivating theories involve statistical manifolds [@amari1983foundation; @amari2016information], stochastic dynamics, and non-equilibrium steady states [@friston2019free]. The catalogue constructs Bernoulli and categorical Fisher geometry, Cramér--Rao and geometric-optimization laws, a finite scalar exponential family with log-partition and KL--Bregman identities, native measure and finite Bayesian inversion, temporal smoothing, causal interventions, finite blankets with a native `CondIndepFun` transfer, hierarchical kernels, and a divergence-free nonequilibrium current. H1 additionally closes one full-support stationary blanket and selected-kernel invariance result on a sixteen-state Boolean internal--sensory--active--external carrier. The package still stops short of arbitrary smooth connections and curvature, generic blanket existence, general causal identification, and continuous-state SDE/PDE steady-state theory. The semantic audit records that boundary theorem by theorem. See [@sec:mathlib4_and_measure_theoretic_probability] and the generated formalism coverage map.

### Langevin Dynamics and the Fokker–Planck Equation {#sec:sophisticated_langevin_fp}

Beyond the static-bound formulation of the FEP, adaptive systems are naturally described by *stochastic* dynamics on the variational parameters. The canonical continuous-time object is the overdamped **Langevin stochastic differential equation**:

$$
\dot{x}(t) \;=\; -\,\nabla F(x(t)) \;+\; \sqrt{2D}\,\xi(t), \qquad \langle \xi(t) \rangle = 0, \;\; \langle \xi(t)\,\xi(t')^\top \rangle = \mathbb{I}\,\delta(t - t'),
$$ {#eq:sd_langevin_sde}

where $F : \mathbb{R}^n \to \mathbb{R}$ is the free-energy functional, $D \ge 0$ is the diffusion coefficient, and $\xi$ is standard Gaussian white noise. [@eq:sd_langevin_sde] expresses the principle that adaptive parameters *drift* along the free-energy gradient while continuously exploring a neighborhood of the current state—reconciling deterministic gradient flow ([@sec:sophisticated_gradient_measure]) with Bayesian posterior sampling.

The probability density $\rho(x, t)$ of trajectories solving [@eq:sd_langevin_sde] evolves according to the **Fokker–Planck equation**:

$$
\partial_t \rho(x, t) \;=\; \nabla \cdot \bigl(\rho\,\nabla F\bigr) \;+\; D\,\nabla^2 \rho \;=\; -\nabla \cdot J(x, t),
$$ {#eq:sd_fokker_planck}

with probability current $J = -\rho\,\nabla F - D\,\nabla \rho$. Under normalizability, boundary, regularity, and constant positive-diffusion assumptions, a zero-current stationary solution has Gibbs form $\rho^\star(x) \propto \exp(-F(x)/D)$. This links the chosen potential to a Boltzmann weight; it does not by itself identify that potential with variational free energy ([@sec:thermodynamics_results]).

### Gradient Flow in Measure Space {#sec:sophisticated_gradient_measure}

A Wasserstein-gradient-flow formulation reinterprets [@eq:sd_fokker_planck] as descent of a free-energy functional on the space of probability measures:

$$
\partial_t \rho \;=\; \nabla \cdot \bigl(\rho\,\nabla \tfrac{\delta F}{\delta \rho}\bigr), \qquad F[\rho] \;=\; \mathbb{E}_\rho[U(x)] \;+\; D\,\mathbb{E}_\rho[\log \rho(x)],
$$ {#eq:sd_wasserstein_flow}

where $\delta F / \delta \rho$ is the $L^2$ functional derivative. [@eq:sd_wasserstein_flow] elevates the FEP from a bound on scalars to a *geometric flow on a manifold of distributions*, with the Wasserstein-2 metric playing the role of Riemannian structure. Topic fep-038 constructs the one-parameter Bernoulli Fisher metric and its inverse-metric natural gradient, while topic fep-018 constructs the corresponding variance-stabilizing coordinate distance. Those finite one-dimensional results are exact; they are not a Wasserstein gradient-flow theorem.

### Ergodicity, Invariant Measures, and Mathlib4 {#sec:sophisticated_ergodicity}

Under an appropriate combination of existence, uniqueness, recurrence, invariant-measure, and integrability hypotheses, a Langevin process may be **ergodic**: time averages then converge to ensemble averages under a stationary measure $\rho^\star$:

$$
\lim_{T \to \infty} \frac{1}{T}\int_0^T \phi(x(t))\,dt \;=\; \int \phi(x)\,\rho^\star(x)\,dx \quad\text{a.s.},
$$ {#eq:sd_ergodicity}

for observables satisfying the theorem's integrability conditions. [@eq:sd_ergodicity] motivates a bridge between single trajectories and ensemble statistics, but no catalogue row defines the continuous-state stochastic process or almost-sure time-average limit needed to prove it. The current Lean sources instead formalize discrete-time measurable semigroups (fep-006), invariant Markov kernels (fep-010), exact discrete two-state relaxation and autocorrelation decay (fep-020 and fep-037), convergent quadratic descent (fep-032), and an exact continuous-time two-state Markov semigroup with master equation and exponential relaxation (fep-149--155). These finite-state results do not imply Langevin ergodicity or a pathwise ergodic theorem.

### Finite Markov Relaxation, Not Langevin (fep-020) {#sec:sophisticated_lean_langevin}

Topic fep-020 defines the normalized symmetric Boolean transition that flips state with probability $\alpha$ and stays put with probability $1-\alpha$. For $0\le\alpha\le1$, every transition mass is nonnegative and each row sums to one. If $p$ is the current mass on `true`, one step is the affine map

$$
T_\alpha(p)=\alpha+(1-2\alpha)p,
\qquad
T_\alpha^{,n}(p)-\tfrac12=(1-2\alpha)^n\bigl(p-\tfrac12\bigr).
$$ {#eq:sd_two_state_relaxation}

Lean proves that $1/2$ is stationary and that $T_\alpha^{,n}(p)\to1/2$ whenever $0<\alpha<1$. The strict interior excludes the alternating endpoint $\alpha=1$ and the frozen endpoint $\alpha=0$. This is an exact finite-state distributional convergence theorem, but not a Langevin discretization. The later fep-149--155 family adds a different exact two-state carrier in continuous time, including a semigroup, master equation, detailed balance, relaxation, and strict Lyapunov witness. H1 uses a further finite refresh semigroup: the selected `true` action chooses its exact positive-time kernel on the sixteen-state Boolean blanket carrier, and repository-real finite KL and Mathlib-native KL to the invariant uniform law both decrease strictly for the same lifted updated posterior. Those inequalities are probabilistic convergence statements, not measured heat, physical entropy production, or universal free-energy dissipation. None of these carriers defines Gaussian noise, a diffusion limit, a continuous-state SDE, or a Fokker--Planck PDE.

### Information Geometry Results ({{areas.InfoGeometry.count}} topics) {#sec:information_geometry_results}

Information geometry treats parametric families of probability distributions $\mathcal{M} = \{p_\theta\}_{\theta \in \Theta}$ as Riemannian manifolds, with the Fisher information tensor as the canonical metric. The {{areas.InfoGeometry.count}} catalogue rows build an exact Bernoulli family deeply, extend it with a categorical score carrier, and add a full-support finite scalar exponential family. The categorical expansion proves Fisher positivity on simplex tangents with explicit full-rank and null directions, pullback, an unbiased scalar Cramér--Rao bound under score regularity, natural-gradient equivariance under an invertible full-rank chart, a mirror-descent three-point identity, an affine-projection Bregman Pythagorean law, and replicator--natural-gradient equivalence. The scalar exponential-family expansion proves normalization, affine log-density ratios, first and second log-partition derivatives, centered scores, Fisher--variance equality, KL--Bregman duality, and interval-local mean-coordinate injection. These finite laws complement native KL, Hellinger, and Bernoulli Fisher--Rao results [@amari1983foundation]. Arbitrary smooth coordinate atlases, multidimensional dual connections, curvature, and general geodesics remain outside scope.

| Topic | Actual Lean content | Semantic disposition | Modules imported (`Mathlib.` prefix omitted) | `sorry` count |
|-------|---------|----------|--------------------------|--------|
| fep-004 | Finite diagonal Fisher metric: symmetry, positive semidefiniteness, and positive definiteness | `{{topics.fep-004.semantic_disposition}}` | {{topics.fep-004.imported_modules}} | 0 |
| fep-014 | Native KL nonnegativity, self-zero, zero characterization, and composition-product chain rule | `{{topics.fep-014.semantic_disposition}}` | {{topics.fep-014.imported_modules}} | 0 |
| fep-017 | Native posterior kernel: normalized fibers, joint reconstruction, prior recovery, and Bayes density | `{{topics.fep-017.semantic_disposition}}` | {{topics.fep-017.imported_modules}} | 0 |
| fep-018 | Bernoulli Fisher--Rao coordinate distance, symmetry, triangle inequality, and separation | `{{topics.fep-018.semantic_disposition}}` | {{topics.fep-018.imported_modules}} | 0 |
| fep-024 | Native KL-regularized objective and its exact zero-weight and self-prior laws | `{{topics.fep-024.semantic_disposition}}` | {{topics.fep-024.imported_modules}} | 0 |
| fep-029 | Quadratic Bregman definition, squared-distance identity, nonnegativity, and point separation | `{{topics.fep-029.semantic_disposition}}` | {{topics.fep-029.imported_modules}} | 0 |
| fep-038 | Bernoulli score, Fisher information and metric, natural gradient, and coordinate pullback | `{{topics.fep-038.semantic_disposition}}` | {{topics.fep-038.imported_modules}} | 0 |
| fep-044 | Bernoulli squared Hellinger divergence: nonnegativity, symmetry, separation, and relabeling invariance | `{{topics.fep-044.semantic_disposition}}` | {{topics.fep-044.imported_modules}} | 0 |
| fep-100 | Categorical Fisher positivity on simplex tangents with rank/null witnesses | `{{topics.fep-100.semantic_disposition}}` | {{topics.fep-100.imported_modules}} | 0 |
| fep-101 | Fisher pullback under a finite reparameterization | `{{topics.fep-101.semantic_disposition}}` | {{topics.fep-101.imported_modules}} | 0 |
| fep-102 | Unbiased scalar Cramér--Rao under score regularity and positive Fisher information | `{{topics.fep-102.semantic_disposition}}` | {{topics.fep-102.imported_modules}} | 0 |
| fep-103 | Natural-gradient equivariance under an invertible full-rank chart | `{{topics.fep-103.semantic_disposition}}` | {{topics.fep-103.imported_modules}} | 0 |
| fep-104 | Mirror-descent three-point identity | `{{topics.fep-104.semantic_disposition}}` | {{topics.fep-104.imported_modules}} | 0 |
| fep-105 | Bregman Pythagorean law for an affine information projection | `{{topics.fep-105.semantic_disposition}}` | {{topics.fep-105.imported_modules}} | 0 |
| fep-106 | Replicator--natural-gradient equivalence on the finite simplex | `{{topics.fep-106.semantic_disposition}}` | {{topics.fep-106.imported_modules}} | 0 |
| fep-142 | Full-support finite scalar exponential-family normalization | `{{topics.fep-142.semantic_disposition}}` | {{topics.fep-142.imported_modules}} | 0 |
| fep-143 | Affine log-density ratio within one supported exponential family | `{{topics.fep-143.semantic_disposition}}` | {{topics.fep-143.imported_modules}} | 0 |
| fep-144 | Log-partition derivative equals the sufficient-statistic mean | `{{topics.fep-144.semantic_disposition}}` | {{topics.fep-144.imported_modules}} | 0 |
| fep-145 | Centered scalar score with zero model expectation | `{{topics.fep-145.semantic_disposition}}` | {{topics.fep-145.imported_modules}} | 0 |
| fep-146 | Log-partition Hessian and Fisher information equal variance, with rank and zero boundaries | `{{topics.fep-146.semantic_disposition}}` | {{topics.fep-146.imported_modules}} | 0 |
| fep-147 | Exponential-family KL equals the log-partition Bregman divergence | `{{topics.fep-147.semantic_disposition}}` | {{topics.fep-147.imported_modules}} | 0 |
| fep-148 | Positive-variance mean coordinate is strictly monotone and injective on an interval | `{{topics.fep-148.semantic_disposition}}` | {{topics.fep-148.imported_modules}} | 0 |
: Information Geometry topics: the Lean content each row actually states, its semantic disposition, the modules its Lean body imports (generated from the body, `Mathlib.` omitted), and its `sorry` count.

#### Fisher Information Metric (fep-004) {#sec:sd_fisher}

On a statistical manifold $\mathcal{M} = \{p_\theta\}_{\theta \in \Theta}$ with $\Theta \subset \mathbb{R}^n$ open, the **Fisher information metric** is the Riemannian metric whose components in the coordinate basis are given by the expected outer product of the score function $s_i(x; \theta) := \partial_{\theta_i} \log p_\theta(x)$:

$$
g_{ij}(\theta) \;=\; \mathbb{E}_{p_\theta}\!\left[\frac{\partial \log p_\theta}{\partial \theta_i} \cdot \frac{\partial \log p_\theta}{\partial \theta_j}\right] \;=\; -\,\mathbb{E}_{p_\theta}\!\left[\frac{\partial^2 \log p_\theta}{\partial \theta_i \partial \theta_j}\right],
$$ {#eq:sd_fisher_metric}

where the second equality uses the identity $\mathbb{E}_{p_\theta}[\partial_i s_j] + \mathbb{E}_{p_\theta}[s_i s_j] = 0$ that follows from differentiating the normalization $\int p_\theta \, d\mu = 1$ twice under the integral. The matrix $I(\theta) = [g_{ij}(\theta)]$ is the **Fisher information matrix** and, under regularity conditions that exchange differentiation and integration, is symmetric and positive semidefinite.

The Fisher metric is distinguished among Riemannian metrics on $\mathcal{M}$ by Chentsov's uniqueness theorem: up to scalar, it is the only metric invariant under sufficient statistics (Markov embeddings). Geometrically, it captures how distinguishable two nearby distributions $p_\theta$ and $p_{\theta + d\theta}$ are: the squared infinitesimal KL divergence is

$$
2\, D_\text{KL}(p_\theta \,\|\, p_{\theta+d\theta}) \;=\; g_{ij}(\theta)\,d\theta^i\,d\theta^j + O(\|d\theta\|^3),
$$ {#eq:sd_kl_fisher_taylor}

so the Fisher metric *is* the Hessian of the KL divergence at coincident parameters — connecting fep-004 directly to fep-014 and fep-024. The **Cramér–Rao bound** states that for any unbiased estimator $T$ of $\theta$, $\operatorname{Var}_{p_\theta}[T] \succeq I(\theta)^{-1}$ in the positive-semidefinite order; no unbiased estimator can resolve parameters more finely than the Fisher geometry permits. In the FEP context, $I(\theta)$ plays the role of a **precision matrix** — the natural metric for measuring how "far" two nearby beliefs are from each other, and the object weighted by attention / synaptic-gain parameters in predictive coding.

The fep-004 row defines a finite diagonal Fisher metric with explicitly supplied information weights and proves symmetry, positive semidefiniteness for nonnegative weights, and positive definiteness for strictly positive weights. The authored composition theorem `fep004_bernoulliMetric_specialization` then shows that its one-coordinate specialization is definitionally the Fisher metric computed in fep-038. fep-100 derives the metric from categorical scores and exposes both full-rank and null directions. fep-102 adds the scalar Cramér--Rao inequality under explicit unbiasedness, score regularity, finite sums, and positive Fisher information; it is not the unrestricted matrix bound quoted above. None of these rows constructs a general smooth manifold or justifies differentiation under an arbitrary integral. See [@sec:catalogue-fep-004] in Appendix B; typeset signatures in [@sec:eqs-fep-004] of [@sec:appendix_c_latex_equations].

#### Natural Gradient (fep-038) {#sec:sd_natural_gradient}

The ordinary Euclidean gradient $\nabla_\theta F$ of a loss $F : \Theta \to \mathbb{R}$ is *not* coordinate-invariant on a statistical manifold: reparameterizing $\theta \mapsto \phi(\theta)$ produces an update that depends on the Jacobian of $\phi$, so two modelers using different parameterizations of the same family will take genuinely different steps. Amari [@amari1998natural] resolved this by defining the **natural gradient** as the steepest-descent direction with respect to the Fisher-induced Riemannian metric:

$$
\tilde{\nabla}_\theta F(\theta) \;=\; I(\theta)^{-1}\,\nabla_\theta F(\theta).
$$ {#eq:sd_natural_gradient}

Geometrically, $\tilde{\nabla}_\theta F$ is the unique vector such that $\langle \tilde{\nabla}_\theta F, v\rangle_{I(\theta)} = dF(\theta)[v]$ for all tangent $v$, where $\langle u, v\rangle_{I} := u^\top I v$ is the Fisher inner product. The natural gradient update

$$
\theta_{t+1} \;=\; \theta_t \;-\; \eta\, I(\theta_t)^{-1}\,\nabla_\theta F(\theta_t)
$$ {#eq:sd_natural_gradient_update}

is coordinate-covariant under the regularity and invertibility assumptions that make the Fisher metric and transformation law well-defined. Its conditioning and statistical-efficiency properties are model- and algorithm-dependent rather than unconditional convergence guarantees. In Active-Inference accounts, $I(\theta_t)^{-1}$ is interpreted as a precision-weighted gain; fep-038 formalizes the inverse-metric update for the Bernoulli family but not that neurobiological interpretation.

The fep-038 row defines the normalized Bernoulli mass, its pointwise parameter derivative, the score, Fisher information as expected squared score, the scalar Fisher metric, and the inverse-metric natural gradient. Lean proves expected-score zero, the closed form $I(p)=1/[p(1-p)]$ on the interior, positive definiteness, metric--natural-gradient duality, and the pullback law through the Fisher--Rao coordinate Jacobian. The maintained foundations generalize the score field to arbitrary finite dimension, prove matrix symmetry, Gram PSD, conditional PD, functorial and positive pullbacks, equivalence of expected-score and matrix-lowered forms, and bilinearity. Under invertibility they construct the unique inverse-Fisher natural gradient and prove metric duality and energy. fep-103 then proves equivariance through an explicitly invertible full-rank chart, and fep-106 identifies the corresponding categorical natural gradient with replicator dynamics on the simplex. Arbitrary smooth atlases, connections, and curvature remain successor work.

#### KL Divergence (fep-014) and the I- / M-Projection Asymmetry {#sec:sd_kl}

The **Kullback–Leibler divergence** between probability measures $q \ll p$ on a measurable space $(X, \mathcal{F})$ is

$$
D_\text{KL}(q \,\|\, p) \;=\; \int_X q\,\log\frac{q}{p}\,d\mu \;=\; \mathbb{E}_q\!\left[\log\frac{dq}{dp}\right].
$$ {#eq:sd_kl_def}

Three structural properties lift it from a mere functional to the canonical statistical discrepancy:

1. **Nonnegativity** (Gibbs' inequality): $D_\text{KL}(q \,\|\, p) \ge 0$ with equality iff $q = p$ a.e. This follows from Jensen's inequality applied to the concave function $\log$: $\mathbb{E}_q[\log(p/q)] \le \log \mathbb{E}_q[p/q] = 0$.

2. **Chain rule**: a joint or kernel-composed divergence decomposes into a marginal term and a conditional term under appropriate finiteness and kernel assumptions.

3. **Data-processing inequality (DPI)**: for a measurable transformation or channel, postprocessing cannot increase KL. This is distinct from the chain rule. The pinned Mathlib revision exposes `InformationTheory.klDiv_comp_right_le`, although it is not part of the fep-014 row's maintained theorem surface.

4. **Asymmetry**: in general $D_\text{KL}(q \,\|\, p) \neq D_\text{KL}(p \,\|\, q)$. This asymmetry is not a defect but carries the **mode-covering / mode-seeking** distinction that governs variational inference:

   - Minimizing the “reverse” direction $D_\text{KL}(q\|p)$ over a restricted approximation family is often described as mode-seeking, but the actual optimizer depends on the family and support constraints.
   - Minimizing the “forward” direction $D_\text{KL}(p\|q)$ is often mass-covering or moment-matching in common exponential-family settings; this too is not a distribution-free theorem.

The common variational form uses $D_\text{KL}(q(s) \,\|\, p(s \mid o))$, but mode-seeking behavior depends on the approximation family and optimization setting and is not itself a theorem in this catalogue. fep-014 directly uses Mathlib's measure-level `InformationTheory.klDiv`. It proves codomain nonnegativity, self-zero under `SigmaFinite`, equality characterization for finite measures, and `klDiv_compProd_eq_add` for finite measures and Markov kernels. The maintained finite information layer separately proves a joint/channel chain rule, independent-product additivity, and the induced prior-marginal bound; the H1 semigroup layer applies Mathlib's native channel DPI to contraction toward an invariant law. These results do not prove the variational projection behavior described above or identify every finite real KL statement with native extended KL.

#### Rényi / Tsallis α-Divergences (fep-044) {#sec:sd_alpha_div}

The one-parameter **Chernoff α-divergence family** interpolates between forward and reverse KL and recovers Hellinger distance at its midpoint:

$$
D_\alpha(p \,\|\, q) \;=\; \frac{1}{\alpha(1-\alpha)}\left[1 - \int p^{\alpha}\, q^{1-\alpha} \, d\mu\right], \qquad \alpha \in (0, 1).
$$ {#eq:sd_alpha_div}

Endpoint limits and distinguished values:

| $\alpha$ | Limit | Behavior |
|--------|-------|-----------|
| $\alpha \to 1$ | $D_\text{KL}(p \,\|\, q)$ | M-projection, mass-covering |
| $\alpha \to 0$ | $D_\text{KL}(q \,\|\, p)$ | I-projection, mode-seeking |
| $\alpha = 1/2$ | $4\,H^2(p, q)$ | Symmetric Hellinger distance squared |
: Endpoint limits and distinguished values of the Renyi/Tsallis $\alpha$-divergence family (fep-044).

The family sits within the broader class of Csiszár $f$-divergences. The fep-044 row selects the distinguished Bernoulli Hellinger instance rather than pretending to cover the entire $\alpha$ family. It defines squared Hellinger divergence with the conventional factor $1/2$ and proves nonnegativity, symmetry, zero iff equal parameters on $[0,1]$, and invariance under exchanging success with failure. Measure-level $\alpha$-divergence, endpoint limits, and general density integration remain separate extensions.

#### Bregman Divergences and Mirror Descent (fep-029) {#sec:sd_bregman}

For a strictly convex, differentiable **potential** $\phi : \mathcal{C} \to \mathbb{R}$ on a convex domain $\mathcal{C} \subseteq \mathbb{R}^n$, the **Bregman divergence** is the gap between $\phi$ and its linear approximation at $q$:

$$
B_\phi(p, q) \;=\; \phi(p) \;-\; \phi(q) \;-\; \langle \nabla \phi(q),\, p - q\rangle.
$$ {#eq:sd_bregman}

Key properties: $B_\phi(p, q) \ge 0$ with equality iff $p = q$; $B_\phi$ is convex in its first argument; and it obeys the **generalized Pythagorean theorem** $B_\phi(p, r) = B_\phi(p, q) + B_\phi(q, r) + \langle \nabla\phi(r) - \nabla\phi(q),\, q - p\rangle$, which reduces to the familiar identity when $q$ is the Bregman projection of $p$ onto a convex set. Distinguished instances:

- $\phi(p) = \tfrac{1}{2}\|p\|^2$ recovers **squared Euclidean distance** $B_\phi(p, q) = \tfrac{1}{2}\|p - q\|^2$.
- $\phi(p) = \sum_i p_i \log p_i$ (negative Shannon entropy) on the probability simplex recovers the **KL divergence** $B_\phi(p, q) = D_\text{KL}(p \,\|\, q)$ — positioning KL as one instance of a general convex-analytic family.
- $\phi(p) = -\log\det(P)$ on positive-definite matrices recovers the **LogDet / Burg divergence** used in covariance estimation.

**Mirror descent** is gradient descent in the dual geometry induced by $\phi$: $\nabla\phi(\theta_{t+1}) = \nabla\phi(\theta_t) - \eta \nabla F(\theta_t)$, with an equivalent proximal form under the usual convexity and regularity conditions. fep-029 defines the one-dimensional quadratic Bregman instance and proves nonnegativity and separation. fep-104 adds the exact mirror-descent three-point identity on its maintained finite inner-product carrier. fep-105 adds an affine-projection Bregman Pythagorean equality under explicit membership, orthogonality, and minimizing premises. These are algebraic and affine finite laws, not a general convergence theorem for mirror descent or existence theorem for projections onto arbitrary convex sets.

#### KL Regularization (fep-024) and Bayesian Update Geometry (fep-017) {#sec:sd_kl_reg_bayes}

Topic fep-024 isolates the elementary log-identities that license variational bounds: the log-ratio decomposition $\log(p/q) = \log p - \log q$, monotonicity of $\log$ on $(0, \infty)$, and the anchor $D_\text{KL}(p \,\|\, p) = 0$ via $\log 1 = 0$. These three facts are the Lean-level primitives behind the ELBO decomposition $\log p(o) = \mathbb{E}_q[\log p(o, s)] - \mathbb{E}_q[\log q(s)] + D_\text{KL}(q \,\|\, p(\cdot \mid o))$ and thus behind every variational FEP bound in the catalogue.

Topic fep-017 now wraps Mathlib's native posterior kernel. Lean proves every posterior fiber has mass one, reconstructs the swapped likelihood--prior joint from predictive mass followed by the posterior, recovers the prior after a Markov likelihood and its posterior, and states the countable-space Radon--Nikodym Bayes-density formula almost everywhere under the predictive law. The row therefore formalizes normalized Bayesian inversion at kernel level. Its remaining geometric extension is to prove a projection characterization for a selected divergence and approximation family.

#### Statistical Manifold Geodesics and Dual Connections (fep-018) {#sec:sd_geodesics}

Amari's information geometry equips $\mathcal{M}$ not with a single Levi–Civita connection but with a one-parameter **α-connection family** $\nabla^{(\alpha)}$, with two distinguished members forming a **dually flat pair** $(\nabla^{(+1)}, \nabla^{(-1)})$:

- The **exponential ($e$-) connection** $\nabla^{(+1)}$: its geodesics are $\log$-linear interpolations $\log p_t = (1-t)\log p_0 + t \log p_1 + \text{const}$. In exponential families these become straight lines in natural parameters.
- The **mixture ($m$-) connection** $\nabla^{(-1)}$: its geodesics are convex mixtures $p_t = (1-t) p_0 + t p_1$, i.e. straight lines in the probability simplex.

Dual connections yield Pythagorean identities under the relevant flatness and projection hypotheses and help explain convergence proofs for particular information-geometric algorithms. The fep-018 row defines the Bernoulli variance-stabilizing coordinate $2\arcsin\sqrt{p}$ and the absolute coordinate difference. It proves nonnegativity, symmetry, the triangle inequality, and separation on the unit interval, giving the exact Fisher--Rao distance for this one-dimensional family. fep-105 supplies a finite affine Bregman Pythagorean law, but neither row defines $\alpha$-connections or geodesic equations on a general manifold, nor identifies its projection with unrestricted measure-valued KL geometry.

**Representative formalization** — *Bernoulli Fisher Geometry (fep-038 with fep-004 and fep-018)*: The family mass differentiates exactly, the expected score vanishes, its Fisher information is $1/[p(1-p)]$, the metric is positive on nonzero tangents, the natural gradient is inverse-metric dual, and the Fisher--Rao coordinate pulls the metric back to Euclidean form. Two authored composition theorems connect the generic finite metric and the distance-separation law to this same family. See [@sec:catalogue-fep-038] in Appendix B and [@sec:eqs-fep-038] in [@sec:appendix_c_latex_equations].

### Bayesian Mechanics Results ({{areas.BayesianMechanics.count}} topics) {#sec:bayesian_mechanics_results}

Bayesian mechanics rests on a particular partition of system states. A **Markov blanket partition** of a finite state space $\mathcal{S}$ is a decomposition into four mutually disjoint blocks $\mathcal{S} = \mathcal{I} \sqcup \mathcal{B}_s \sqcup \mathcal{B}_a \sqcup \mathcal{E}$ — **internal** ($\mathcal{I}$), **sensory blanket** ($\mathcal{B}_s$), **active blanket** ($\mathcal{B}_a$), and **external** ($\mathcal{E}$) — such that internal and external states are conditionally independent given the blanket $\mathcal{B} = \mathcal{B}_s \cup \mathcal{B}_a$:

$$
p(\mu, \eta \mid b) \;=\; p(\mu \mid b)\, p(\eta \mid b), \qquad \mu \in \mathcal{I},\; \eta \in \mathcal{E},\; b \in \mathcal{B}.
$$ {#eq:sd_markov_blanket_ci}

[@eq:sd_markov_blanket_ci] states statistical conditional independence for a specified law. It does not by itself entail causal arrows, sensory/active directionality, or an inference interpretation. Active-Inference graphical and dynamical models add such directional assumptions through their transition structure; NESS treatments add further drift, diffusion, regularity, and stationarity hypotheses. Keeping those additions separate is essential to the blanket critique.

Topic **fep-005** defines four `Finset.filter` blocks from an arbitrary assignment `Fin 20 → Fin 4`, proves disjointness for unequal labels, characterizes membership, and proves that every state belongs to exactly one block. Topic **fep-009** uses Mathlib's conditional-expectation-based `CondIndep` predicate: it proves symmetry and supplies the trivial-σ-algebra case as a concrete inhabitant, while retaining basic measure-mass laws. The topic declarations do not select blanket σ-algebras from fep-005's labels or construct a joint law for a particular system. The maintained `FEP.MarkovBlanket` foundation supplies a separate normalized finite joint, proves [@eq:sd_markov_blanket_ci] at every positive-mass blanket state, proves zero conditional mutual information, and constructs typed nontrivial dynamics. Its factorization theorem is the named formal witness for the reviewed fep-005→fep-009 edge. The `FEP.NativeBlanket` family then embeds normalized finite laws as weighted Dirac measures, proves singleton and expectation reflection, aligns finite prediction with native measure--kernel composition, and proves Mathlib's native `CondIndepFun` for the factorized static blanket, including measurable endpoint coarsening and rowwise transition preservation. The H1 terminal theorem closes one further instance on shared carriers: its full-support uniform law on the sixteen Boolean $(I,S,A,E)$ states factorizes as $P(S,A)P(I\mid S,A)P(E\mid S,A)$ and is invariant under the exact refresh kernel selected by the emitted `true` action. This does not turn an arbitrary partition or transition into a generic blanket-existence theorem, prove rowwise blanket preservation, identify causal direction from observational factorization, or establish a biological boundary.

In a NESS decomposition, skew-symmetry of a current supplies cancellations, but antisymmetry alone does not imply a continuous-space stationarity equation for an arbitrary field and density. Topic fep-025 now defines finite probability current as forward flow minus reverse flow, defines its divergence, proves antisymmetry and global conservation, and shows that a normalized transition matrix with a stationary distribution has zero divergence at every state. A directed three-state cycle witnesses the genuinely non-equilibrium case: its current is divergence-free yet nonzero, so stationarity does not force detailed balance. The row does not claim a diffusion, density PDE, or continuous Helmholtz decomposition; see [@sec:thermodynamics_results].

**Mathlib4 module footprint (Bayesian Mechanics)**: The area now uses several concrete backbones. Finite partitions and probability currents use `Finset` and `Matrix`; blanket independence reaches `Probability.Independence.Conditional`; reversibility reaches `Probability.Kernel.Invariance`; posterior, predictive, and hierarchical laws use native kernel composition and composition products; empirical-prior estimation uses `Probability.Distributions.Binomial` plus exact sequence limits. Gaussian laws and derivatives use `Probability.Distributions.Gaussian.Real` and `Analysis.SpecialFunctions.Log.Deriv`. These imports expose real structures, while the authored cross-topic theorems certify which structures actually compose.

| Topic | Actual Lean content | Semantic disposition | Modules imported (`Mathlib.` prefix omitted) | `sorry` count |
|-------|---------|----------|--------------------------|--------|
| fep-005 | Four-label finite partition with disjointness and unique total membership | `{{topics.fep-005.semantic_disposition}}` | {{topics.fep-005.imported_modules}} | 0 |
| fep-009 | Conditional-independence symmetry and a trivial-σ-algebra witness, plus basic measure laws | `{{topics.fep-009.semantic_disposition}}` | {{topics.fep-009.imported_modules}} | 0 |
| fep-010 | Reversible Markov kernel implies invariant measure; identity-kernel witness and invariant composition | `{{topics.fep-010.semantic_disposition}}` | {{topics.fep-010.imported_modules}} | 0 |
| fep-019 | Native prior-predictive measure, mass preservation, normalization, and sequential association | `{{topics.fep-019.semantic_disposition}}` | {{topics.fep-019.imported_modules}} | 0 |
| fep-027 | Normalized hierarchical joint, exact marginals, and three-level associativity | `{{topics.fep-027.semantic_disposition}}` | {{topics.fep-027.imported_modules}} | 0 |
| fep-022 | Posterior-predictive kernel plus exact proper Bernoulli Brier-score decomposition | `{{topics.fep-022.semantic_disposition}}` | {{topics.fep-022.imported_modules}} | 0 |
| fep-036 | Finite binomial sampling, outcome-indexed Laplace prior, shrinkage identity, and consistency transfer | `{{topics.fep-036.semantic_disposition}}` | {{topics.fep-036.imported_modules}} | 0 |
| fep-040 | Native Gaussian law and moments; entropy monotonicity, derivatives, and heat capacity | `{{topics.fep-040.semantic_disposition}}` | {{topics.fep-040.imported_modules}} | 0 |
| fep-042 | Bernoulli sufficient statistic and exact likelihood factorization | `{{topics.fep-042.semantic_disposition}}` | {{topics.fep-042.imported_modules}} | 0 |
| fep-046 | Recursive finite stick weights, exact mass conservation, and residual bounds | `{{topics.fep-046.semantic_disposition}}` | {{topics.fep-046.imported_modules}} | 0 |
| fep-135 | Weighted-Dirac embedding preserves singleton masses and normalization | `{{topics.fep-135.semantic_disposition}}` | {{topics.fep-135.imported_modules}} | 0 |
| fep-136 | Embedded finite laws are injective and preserve finite expectations | `{{topics.fep-136.semantic_disposition}}` | {{topics.fep-136.imported_modules}} | 0 |
| fep-137 | Embedded finite prediction agrees with native measure--kernel composition | `{{topics.fep-137.semantic_disposition}}` | {{topics.fep-137.imported_modules}} | 0 |
| fep-138 | Embedded static blanket law has exact rectangle factorization | `{{topics.fep-138.semantic_disposition}}` | {{topics.fep-138.imported_modules}} | 0 |
| fep-139 | Factorized static blanket satisfies native `CondIndepFun`, with a correlated nontrivial witness | `{{topics.fep-139.semantic_disposition}}` | {{topics.fep-139.imported_modules}} | 0 |
| fep-140 | Measurable endpoint maps preserve native blanket conditional independence | `{{topics.fep-140.semantic_disposition}}` | {{topics.fep-140.imported_modules}} | 0 |
| fep-141 | A factorized finite transition row preserves the native blanket property | `{{topics.fep-141.semantic_disposition}}` | {{topics.fep-141.imported_modules}} | 0 |
: Bayesian Mechanics topics: the Lean content each row actually states, its semantic disposition, the modules its Lean body imports (generated from the body, `Mathlib.` omitted), and its `sorry` count.

#### Hierarchical Generative Models and Predictive Coding (fep-027) {#sec:sd_hierarchical}

A **hierarchical generative model** of depth $L$ over observations $o$ and latent state stacks $s^{(1)}, \ldots, s^{(L)}$ factors the joint as a Markov chain on levels:

$$
p\!\left(o, s^{(1)}, \ldots, s^{(L)}\right) \;=\; p(o \mid s^{(1)}) \;\prod_{l=1}^{L-1} p(s^{(l)} \mid s^{(l+1)}) \;\cdot\; p(s^{(L)}).
$$ {#eq:sd_hierarchical_gm}

In Friston's predictive coding realization, each conditional $p(s^{(l)} \mid s^{(l+1)})$ is Gaussian, $s^{(l)} = g^{(l)}(s^{(l+1)}) + \omega^{(l)}$ with $\omega^{(l)} \sim \mathcal{N}(0, \Pi_l^{-1})$, so that inference reduces to gradient descent on precision-weighted squared prediction errors $\varepsilon^{(l)} = s^{(l)} - g^{(l)}(\mu^{(l+1)})$. This gives the canonical **top-down predictions / bottom-up prediction errors** dynamic:

$$
\dot\mu^{(l)} \;=\; -\,\Pi_l\,\varepsilon^{(l)} \;+\; \partial_{\mu^{(l)}} g^{(l-1)}\,\Pi_{l-1}\,\varepsilon^{(l-1)},
$$ {#eq:sd_predictive_coding_dynamics}

a neurobiologically suggestive message-passing algorithm in which precisions $\Pi_l$ gate the influence of each level. Marginalization preserves probability mass only after the joint law, measurability, and normalization hypotheses have been supplied.

The fep-027 row defines a hierarchical joint as Mathlib's native measure--kernel composition product. Probability parents and Markov child kernels give mass one; the first marginal recovers the parent; the second marginal is exactly the prior-predictive law; and a three-level hierarchy is associative up to the canonical measurable product equivalence. The authored `fep027_priorPredictive_is_fep019` theorem connects its child marginal to fep-019 without copying either definition. The row does not yet represent arbitrary-depth dependent products or the Gaussian conditional kernels in [@eq:sd_hierarchical_gm].

#### Gaussian Entropy, Variance as Temperature, and Heat Capacity (fep-040) {#sec:sd_gaussian_entropy}

For a univariate Gaussian $\mathcal{N}(\mu, \sigma^2)$ the differential entropy admits the closed form

$$
H(\mathcal{N}(\mu, \sigma^2)) \;=\; \tfrac{1}{2}\log(2\pi e\, \sigma^2) \;=\; \tfrac{1}{2}\log(2\pi e) + \tfrac{1}{2}\log \sigma^2,
$$ {#eq:sd_gauss_entropy}

with multivariate generalization $H(\mathcal{N}(\mu, \Sigma)) = \tfrac{1}{2}\log\det(2\pi e\,\Sigma)$. Entropy is monotone in the variance — higher $\sigma^2$ encodes higher uncertainty. The **equipartition / heat-capacity** analogy is the bridge to statistical mechanics: identify $\sigma^2$ with thermodynamic temperature $T$ (each quadratic degree of freedom carries $\tfrac{1}{2}k_B T$ of energy at equilibrium), so that

$$
U \;=\; \langle F\rangle \;=\; \tfrac{1}{2}k_B T, \qquad C_V \;=\; \frac{\partial U}{\partial T} \;=\; \tfrac{1}{2}k_B, \qquad S \;=\; \int \frac{C_V}{T}\,dT \;=\; \tfrac{1}{2}k_B \log T + \text{const}.
$$ {#eq:sd_equipartition_thermo}

The shared logarithmic form motivates an **analogy** between variance and temperature after choosing units and a concrete probabilistic/thermodynamic model. It is not an identity of physical quantities: belief variance need not have temperature units, and precision need not be a thermodynamic inverse temperature. The catalogue does not formalize that model bridge.

The fep-040 row wraps Mathlib's normalized real Gaussian law and proves its total mass, mean, and variance from native theorems. It defines the one-dimensional positive-variance entropy formula, proves strict monotonicity and derivative $1/(2v)$, then composes variance $v=\kappa T$ to obtain entropy derivative $1/(2T)$ and dimensionless heat capacity $1/2$. The authored `fep013_gaussianHelmholtz_derivative` theorem feeds this entropy into the Helmholtz first-law identity. The remaining boundary is multivariate covariance/determinant entropy and a physical units model, not the absence of a Gaussian object.

#### Stick-Breaking Priors and Dirichlet Processes (fep-046) {#sec:sd_stick_breaking}

Sethuraman's **stick-breaking construction** gives an explicit, almost-surely-valid sample from a **Dirichlet process** $\mathrm{DP}(\alpha, G_0)$:

$$
V_k \;\stackrel{\text{iid}}{\sim}\; \mathrm{Beta}(1, \alpha), \qquad \pi_k \;=\; V_k\,\prod_{j<k}(1 - V_j), \qquad \theta_k \;\stackrel{\text{iid}}{\sim}\; G_0, \qquad G \;=\; \sum_{k=1}^\infty \pi_k\,\delta_{\theta_k}.
$$ {#eq:sd_stick_breaking}

The construction proceeds by iteratively "breaking" a unit stick: at step $k$, fraction $V_k$ of the remaining stick $\prod_{j<k}(1 - V_j)$ is assigned to component $k$. Two algebraic invariants make this well-posed: the retained mass $v(1-v) \in [0, 1]$ is nonnegative (each break gives a valid proportion), and the remaining stick $\prod_{j \le k}(1 - V_j)$ decreases monotonically in $k$ (monotone convergence to zero a.s. when $\alpha < \infty$), so $\sum_k \pi_k = 1$ almost surely. The resulting random measure $G$ is a draw from $\mathrm{DP}(\alpha, G_0)$; the concentration parameter $\alpha$ controls the rate at which new atoms appear (small $\alpha$ = few large atoms, large $\alpha$ = many small atoms following $G_0$).

Dirichlet processes are the foundational prior of **Bayesian nonparametrics**: they place a prior over discrete probability measures whose support size is itself random and grows with data. In Active Inference, DP priors enable **infinite-dimensional generative models** that can add latent causes as observations demand — a formalization of conceptual novelty and structure learning. The Chinese-restaurant-process representation of the same prior gives a coherent sampling / inference scheme (Neal's Algorithm 8 for DP mixtures). Hierarchical Dirichlet processes (HDPs) extend this to shared-atom structure across groups (topic models, multi-task learning), and Pitman–Yor processes generalize to power-law atom-size distributions relevant to linguistic data.

The fep-046 row recursively defines every allocated weight and the residual mass for an arbitrary finite list of breaks. Lean proves the exact conservation identity “allocated mass plus remainder equals one” without inequality assumptions, then proves the remainder lies in $[0,1]$ when every break fraction lies in $[0,1]$. This completes the finite stick-breaking algebra. It does not certify an infinite random sequence, almost-sure vanishing of the remainder, or a Dirichlet-process law; those require a distribution on breaks and countable-limit theory.

**Representative formalization** — *Finite Label Partition (fep-005)*: Given an assignment from twenty states to four labels, the row defines each block with `Finset.filter`, proves unequal labels give disjoint blocks, characterizes membership, and proves existence and uniqueness of the block containing every state. It does not prove conditional independence or that any dynamical system admits a Markov blanket. The distinction is central to the Biehl et al. discussion ([@sec:blanket_conditions_biehl_et_al]). See [@sec:catalogue-fep-005] in Appendix B and [@sec:eqs-fep-005] in [@sec:appendix_c_latex_equations].

**Representative formalization** — *Hierarchical Generative Models (fep-027)*: Hierarchical models sit at the junction of Bayesian mechanics and measure-theoretic probability. The row uses Mathlib's composition product $\mu \otimes_m \kappa$ rather than an independent product measure: it proves normalization under probability/Markov hypotheses, exact parent and predictive marginals, and associativity of a third conditional level. This is a kernel-valued hierarchy with real conditional dependence, while a particular predictive-coding factorization and blanket structure remain model choices.

### Synthesis: What the {{combined_info_bayes_count}} Rows Establish {#sec:sophisticated_synthesis}

Taken together, the {{areas.InfoGeometry.count}} Information Geometry rows and {{areas.BayesianMechanics.count}} Bayesian Mechanics rows map a broad set of probabilistic and geometric interfaces. They do not yet span the full infrastructure required for a complete FEP formalization.

**The {{areas.InfoGeometry.count}} Information Geometry theorems** establish the **differential-geometric substrate**:

- **Fisher geometry** — fep-038 derives the Bernoulli score, Fisher information and natural gradient; fep-004 abstracts its finite weighted metric; fep-018 gives the corresponding coordinate distance and separation law.
- **Categorical and optimization geometry** — fep-100--106 establish simplex-tangent Fisher positivity, pullback, scalar Cramér--Rao, invertible-chart natural-gradient equivariance, mirror-descent and affine Bregman identities, and replicator equivalence with full-rank and null boundaries.
- **Scalar exponential-family geometry** — fep-142--148 establish full-support normalization, affine log-density ratios, log-partition differentiation, centered scores, Fisher--variance equality, KL--Bregman duality, and interval-local mean-coordinate injection, with nonconstant positive-rank and constant-statistic zero boundaries.
- **Core information divergence** — fep-014 proves native KL laws and a composition-product chain rule; fep-024 proves scalar log identities rather than another KL definition.
- **Divergence layers** — fep-029 treats the exact scalar quadratic Bregman instance; fep-044 constructs Bernoulli squared Hellinger divergence; fep-104/fep-105 add finite mirror and affine-projection identities; fep-014 provides native measure KL.
- **Metric-space realization** — fep-018 proves Bernoulli Fisher--Rao nonnegativity, symmetry, triangle inequality, and separation, without claiming general $\alpha$-geodesics.
- **Normalized Bayesian inversion** — fep-017 uses Mathlib's posterior kernel and proves normalization, reconstruction, recovery, and a countable Bayes-density law.

**The {{areas.BayesianMechanics.count}} Bayesian Mechanics theorems** establish the **probabilistic substrate**:

- **Finite partitions** — fep-005 proves a four-label disjoint cover with unique membership but not the conditional-independence structure $p(\mu,\eta\mid b) = p(\mu\mid b)p(\eta\mid b)$.
- **Conditional independence and measure substrates** — fep-009 proves generic `CondIndep` symmetry and a trivial-σ-algebra witness. The maintained blanket foundation connects the fep-005-style four-block structure to a normalized finite law, positive-mass conditional factorization, zero conditional mutual information, and typed nontrivial dynamics. fep-135--141 embed this carrier into native measures and prove one concrete sigma-algebra-valued `CondIndepFun` statement, measurable endpoint coarsening, and rowwise transition preservation. H1 adds one full-support factorized stationary law and proves invariance under its selected positive-time refresh kernel. Generic blanket existence, arbitrary-mixture closure, causal identification, and biological interpretation remain absent.
- **Predictive and hierarchical kernels** — fep-019 and fep-027 prove native normalized prediction, exact marginals, and associativity; fep-022 adds posterior prediction and a proper Brier-score decomposition.
- **Measure and finite Bayesian inversion** — fep-051--057 cover Radon--Nikodym reconstruction, posterior-kernel swapping and disintegration at their stated measure-theoretic scopes, plus finite normalization, Bayes reconstruction, conjugacy, and zero-evidence boundaries.
- **Temporal inference** — fep-072--078 prove finite forward filtering, backward information, smoothing, normalized variational updates, hierarchical prediction, and model averaging.
- **Causal blankets and interventions** — fep-079--085 connect finite blanket factorization, conditional mutual information, ordered parent factorization, intervention kernels, non-descendant invariance, and local Markov laws while retaining explicit zero-evidence and identification limits.
- **Finite stick arithmetic** — fep-046 proves exact allocated-plus-residual mass conservation and unit-interval residual bounds, while leaving the infinite random process open.
- **Sufficient statistics** — fep-042 proves Bernoulli Fisher--Neyman factorization through success and failure counts.
- **Empirical-prior model** — fep-036 defines a finite binomial sampling PMF and its outcome-indexed Laplace prior, proves interiority, monotonicity, exact shrinkage, and deterministic consistency transfer, and composes the estimate with a normalized Bernoulli posterior. The statistical-convergence foundation supplies almost-sure Boolean and finite-atom strong laws, a whole-law $L^1$ limit, and convergence of every finite observable. The learning family supplies concentration and model-evidence laws, while fep-121--127 add finite-law squared/Brier-risk and bad-event transfer for the same Laplace estimator. H1 proves posterior bad-mass contraction for a separate selected Boolean sampling model; contraction for the Laplace estimator or broader model classes, minimax or empirical calibration, and a marginal-likelihood optimum remain open.
- **Gaussian thermodynamics** — fep-040 constructs the native Gaussian law and moments and proves entropy/temperature derivatives and heat capacity in one dimension.
- **Finite-state stationarity** — fep-010 proves that measure--kernel detailed balance implies invariance, witnesses reversibility with the identity Markov kernel, and proves invariant-kernel composition. The finite path family adds fluctuation and dissipation laws; fep-149--155 add an exact two-state continuous-time semigroup, master equation, detailed balance, relaxation, and Lyapunov decay. These do not establish irreducibility in general, continuous-state stochastic dynamics, or pathwise SDE theory.

The intended theory interlocks information geometry with probabilistic generative, temporal, causal, and conditional-independence structures. The topic rows and maintained foundations close several interfaces explicitly: score expectations produce categorical Fisher geometry, pullbacks, scalar Cramér--Rao, chart-qualified natural gradients, and finite scalar exponential-family dual identities; posterior kernels compose with prediction, hierarchy, smoothing, and model averaging; finite blanket laws connect to interventions, local Markov structure, and one native `CondIndepFun` transfer; and empirical-law limits coexist with finite concentration, risk-transfer, and evidence bounds. H1 adds one end-to-end finite instance in which a learned and further-updated posterior is lifted to the same blanket carrier used by a posterior-dependent action, invariant refresh dynamics, and strict real/native KL decrease. The remaining frontiers are multidimensional smooth manifolds and dual connections, generic blanket existence and measure-level causal identification, continuous-state SDE/PDE semantics, infinite random measures, and posterior contraction or empirical calibration beyond the selected Boolean learning model. {{combined_info_bayes_count_caps}} catalogue rows therefore provide both breadth and deep executable instances without presenting finite closure as causal identification, physical thermodynamic dissipation, empirical adequacy, or a universal FEP theorem.
