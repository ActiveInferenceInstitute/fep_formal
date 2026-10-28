module
public import Init

@[expose] public section
/-!
# GNN v1.1 document surface: typed AST and decidable well-formedness

Direction-2 Q1 slice of the fep_lean/GNN bridge (`specs/gnn-bridge-q1-syntax-ast`).
The object language is the sectioned Markdown surface normatively defined by
`GeneralizedNotationNotation/doc/gnn/gnn_syntax.md` and evidenced by the four
canonical exemplars under `input/gnn_files/{discrete,continuous}`: the
required sections `GNNSection`, `GNNVersionAndFlags`, `ModelName`,
`StateSpaceBlock`, and `Connections`, plus the optional sections
`ModelAnnotation`, `InitialParameterization`, `Equations`, `Time`,
`ActInfOntologyAnnotation`, `ModelParameters`, `Footer`, and `Signature`,
each carried as a typed wrapper.

Q1 covers syntax and mechanical well-formedness only: section presence,
canonical order, and at-most-once per kind; the connection token grammar; and
the decidable fragment of dimension consistency (positive literal dimensions;
dimension name references resolving to a declared variable or a
`ModelParameters` key). Numeric dimension/parameter-value agreement,
`InitialParameterization` value semantics, version-gated feature enforcement,
ontology-term vocabulary validation, and model-kind detection are deferred to
later slices. Compilation of this module establishes nothing about GNN
runtime behavior (bridge-contract evidence firewall, section 7).
-/

namespace FEP.GnnDocument

/-! ## Sections and typed wrappers -/

/-- Syntax version pinned by a `GNNVersionAndFlags` section. -/
inductive GnnVersion where
  | v1
  | v1_0
  | v1_1

/-- The frozen section inventory in canonical document order. -/
inductive GnnSectionKind where
  | gnnSection
  | gnnVersionAndFlags
  | modelName
  | modelAnnotation
  | stateSpaceBlock
  | connections
  | initialParameterization
  | equations
  | time
  | actInfOntologyAnnotation
  | modelParameters
  | footer
  | signature
  deriving BEq, DecidableEq

/-- Canonical rank of a section kind: its position in the frozen order. -/
def GnnSectionKind.rank : GnnSectionKind → Nat
  | .gnnSection => 0
  | .gnnVersionAndFlags => 1
  | .modelName => 2
  | .modelAnnotation => 3
  | .stateSpaceBlock => 4
  | .connections => 5
  | .initialParameterization => 6
  | .equations => 7
  | .time => 8
  | .actInfOntologyAnnotation => 9
  | .modelParameters => 10
  | .footer => 11
  | .signature => 12

/-- Declared value type of a state-space variable (`type=<type>`). -/
inductive GnnValueType where
  | floatT
  | intT
  | boolT

/-- One dimension entry: a positive integer literal or a name reference. -/
inductive GnnDim where
  | lit (n : Nat)
  | ref (name : String)

/-- One `StateSpaceBlock` declaration `NAME[dims..., key=value...]`. The
`defaultValue` hint is a v1.1 extension stored verbatim, never validated. -/
structure GnnDecl where
  name : String
  dims : List GnnDim
  valueType : GnnValueType
  defaultValue : Option String

/-- Direction token of a connection edge. -/
inductive ConnKind where
  | directed
  | undirected

/-- One `Connections` edge `A>B`, `A-B`, optionally annotated `:label`. -/
structure GnnConnection where
  src : String
  kind : ConnKind
  dst : String
  label : Option String

/-- One `InitialParameterization` entry: the declared variable it
parameterizes plus the verbatim brace payload. Payloads carry no Q1
semantics; value-level conformance is a later slice. -/
structure GnnParamEntry where
  varName : String
  payload : String

/-- One `Time` line: `Key=Value` or a bare token. -/
structure GnnTimeEntry where
  key : String
  value : Option String

/-- One `ActInfOntologyAnnotation` binding `Variable=Term`. Terms are kept
verbatim; vocabulary validation is parameterized by the frozen GNN
vocabulary in a later slice. -/
structure GnnBinding where
  varName : String
  term : String

/-- One `ModelParameters` line `key: value`; values stay verbatim scalars. -/
structure GnnParameter where
  key : String
  value : String

/-- A section: the kind tag with its typed wrapper payload. -/
inductive GnnSection where
  | gnnSection (identifier : String)
  | gnnVersionAndFlags (version : GnnVersion) (flags : List String)
  | modelName (name : String)
  | modelAnnotation (text : String)
  | stateSpaceBlock (decls : List GnnDecl)
  | connections (edges : List GnnConnection)
  | initialParameterization (entries : List GnnParamEntry)
  | equations (text : String)
  | time (entries : List GnnTimeEntry)
  | actInfOntologyAnnotation (bindings : List GnnBinding)
  | modelParameters (params : List GnnParameter)
  | footer (text : String)
  | signature (text : String)

/-- The kind tag of a section. -/
def GnnSection.kind : GnnSection → GnnSectionKind
  | .gnnSection _ => .gnnSection
  | .gnnVersionAndFlags _ _ => .gnnVersionAndFlags
  | .modelName _ => .modelName
  | .modelAnnotation _ => .modelAnnotation
  | .stateSpaceBlock _ => .stateSpaceBlock
  | .connections _ => .connections
  | .initialParameterization _ => .initialParameterization
  | .equations _ => .equations
  | .time _ => .time
  | .actInfOntologyAnnotation _ => .actInfOntologyAnnotation
  | .modelParameters _ => .modelParameters
  | .footer _ => .footer
  | .signature _ => .signature

/-- A sectioned GNN document: ordered sections, each kind at most once. -/
structure GnnDocument where
  sections : List GnnSection

/-! ## Token grammar -/

/-- A name character: alphanumeric, `_`, `π`, or `'` (syntax doc §2). -/
def isValidNameChar (c : Char) : Bool :=
  c.isAlphanum || c == '_' || c == 'π' || c == '\''

/-- A GNN name: nonempty, all name characters. Applies to variable names,
section identifiers, connection endpoints, annotation labels, and
`ModelParameters` keys. -/
def isValidGnnName (s : String) : Bool :=
  !s.isEmpty && s.toList.all isValidNameChar

/-! ## Decidable well-formedness -/

/-- The required section kinds. -/
def requiredSectionKinds : List GnnSectionKind :=
  [.gnnSection, .gnnVersionAndFlags, .modelName, .stateSpaceBlock, .connections]

/-- Section kinds of a document, in document order. -/
def sectionKinds (doc : GnnDocument) : List GnnSectionKind :=
  doc.sections.map GnnSection.kind

/-- Every required section kind occurs (GNN-E001). -/
def requiredSectionsPresent (doc : GnnDocument) : Bool :=
  requiredSectionKinds.all fun k => (sectionKinds doc).contains k

/-- Ranks strictly increase along the list. -/
def ranksStrictlyIncreasing : List Nat → Bool
  | [] => true
  | [_] => true
  | a :: b :: rest => decide (a < b) && ranksStrictlyIncreasing (b :: rest)

/-- Sections appear in canonical order, each kind at most once. -/
def sectionsInCanonicalOrder (doc : GnnDocument) : Bool :=
  ranksStrictlyIncreasing ((sectionKinds doc).map GnnSectionKind.rank)

/-- A dimension entry is well formed: positive literal or valid name
reference. -/
def dimWellFormed : GnnDim → Bool
  | .lit n => decide (0 < n)
  | .ref name => isValidGnnName name

/-- A declaration is well formed in isolation. -/
def declWellFormed (d : GnnDecl) : Bool :=
  isValidGnnName d.name && d.dims.all dimWellFormed

/-- No duplicate names along the list (GNN-E004 on declarations). -/
def noDuplicateNames : List String → Bool
  | [] => true
  | a :: rest => !(rest.contains a) && noDuplicateNames rest

/-- Connection token grammar: valid endpoint names and, when present, a
valid annotation label (syntax doc §3). -/
def connectionWellFormed (e : GnnConnection) : Bool :=
  isValidGnnName e.src && isValidGnnName e.dst && e.label.all isValidGnnName

/-- Mechanical per-section rules of the frozen surface. Free-text wrappers
carry no constraint; `Time` entries have no frozen grammar beyond the
key/value record shape. -/
def sectionContentWellFormed : GnnSection → Bool
  | .gnnSection identifier => isValidGnnName identifier
  | .gnnVersionAndFlags _ _ => true
  | .modelName _ => true
  | .modelAnnotation _ => true
  | .stateSpaceBlock decls =>
      decls.all declWellFormed && noDuplicateNames (decls.map GnnDecl.name)
  | .connections edges => edges.all connectionWellFormed
  | .initialParameterization entries =>
      entries.all fun e => isValidGnnName e.varName
  | .equations _ => true
  | .time _ => true
  | .actInfOntologyAnnotation bindings =>
      bindings.all fun b => isValidGnnName b.varName
  | .modelParameters params => params.all fun p => isValidGnnName p.key
  | .footer _ => true
  | .signature _ => true

/-! ## Cross-section extraction -/

/-- State-space declarations across the document. -/
def stateSpaceDecls (doc : GnnDocument) : List GnnDecl :=
  (doc.sections.filterMap fun
    | .stateSpaceBlock decls => some decls
    | _ => none).flatten

/-- Declared variable names. -/
def declaredNames (doc : GnnDocument) : List String :=
  stateSpaceDecls doc |>.map GnnDecl.name

/-- Connection edges across the document. -/
def connectionEdges (doc : GnnDocument) : List GnnConnection :=
  (doc.sections.filterMap fun
    | .connections edges => some edges
    | _ => none).flatten

/-- `ModelParameters` entries across the document. -/
def modelParameters (doc : GnnDocument) : List GnnParameter :=
  (doc.sections.filterMap fun
    | .modelParameters params => some params
    | _ => none).flatten

/-- `ModelParameters` keys. -/
def parameterKeys (doc : GnnDocument) : List String :=
  modelParameters doc |>.map GnnParameter.key

/-- `InitialParameterization` entries across the document. -/
def parameterizationEntries (doc : GnnDocument) : List GnnParamEntry :=
  (doc.sections.filterMap fun
    | .initialParameterization entries => some entries
    | _ => none).flatten

/-- `ActInfOntologyAnnotation` bindings across the document. -/
def ontologyBindings (doc : GnnDocument) : List GnnBinding :=
  (doc.sections.filterMap fun
    | .actInfOntologyAnnotation bindings => some bindings
    | _ => none).flatten

/-! ## Cross-section consistency -/

/-- Dimension name references resolve to a declared variable or a
`ModelParameters` key. This is the decidable mechanical fragment of
dimension consistency; the numeric reading of a reference is deferred. -/
def dimRefsResolve (doc : GnnDocument) : Bool :=
  let names := declaredNames doc
  let keys := parameterKeys doc
  stateSpaceDecls doc |>.all fun d =>
    d.dims.all fun
      | .lit _ => true
      | .ref name => names.contains name || keys.contains name

/-- Every connection endpoint is a declared variable (GNN-E003, strict
under the frozen surface). -/
def connectionsReferenceDecls (doc : GnnDocument) : Bool :=
  let names := declaredNames doc
  connectionEdges doc |>.all fun e =>
    names.contains e.src && names.contains e.dst

/-- Every parameterized variable is declared (GNN-W003, strict under the
frozen surface). -/
def parameterizationVarsDeclared (doc : GnnDocument) : Bool :=
  let names := declaredNames doc
  parameterizationEntries doc |>.all fun e => names.contains e.varName

/-- Every ontology binding variable is declared. Terms stay verbatim. -/
def ontologyVarsDeclared (doc : GnnDocument) : Bool :=
  let names := declaredNames doc
  ontologyBindings doc |>.all fun b => names.contains b.varName

/-! ## Document-level well-formedness -/

/-- Well-formedness of a document under the frozen Q1 surface: required
section presence, canonical order with at-most-once per kind, per-section
token grammar, and the decidable cross-section consistency rules. -/
def documentWellFormed (doc : GnnDocument) : Bool :=
  requiredSectionsPresent doc
    && sectionsInCanonicalOrder doc
    && doc.sections.all sectionContentWellFormed
    && dimRefsResolve doc
    && connectionsReferenceDecls doc
    && parameterizationVarsDeclared doc
    && ontologyVarsDeclared doc

/-- Well-formedness as a proposition, decided by `documentWellFormed`. -/
def WellFormed (doc : GnnDocument) : Prop :=
  documentWellFormed doc = true

instance wellFormedDecidable (doc : GnnDocument) :
    Decidable (WellFormed doc) :=
  inferInstanceAs (Decidable (documentWellFormed doc = true))

/-! ## Exemplar smoke values -/

/-- Discrete POMDP excerpt (`actinf_pomdp_agent.md`): exercises a named
dimension reference that forward-references `π`, mixed int/float value
types, and the optional-section inventory. -/
def actinfPomdpExcerpt : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Active Inference POMDP Agent"
    , .modelAnnotation "Discrete POMDP agent excerpt"
    , .stateSpaceBlock
        [ ⟨"A", [.lit 3, .lit 3], .floatT, none⟩
        , ⟨"B", [.lit 3, .lit 3, .lit 3], .floatT, none⟩
        , ⟨"C", [.lit 3], .floatT, none⟩
        , ⟨"D", [.lit 3], .floatT, none⟩
        , ⟨"E", [.lit 3], .floatT, none⟩
        , ⟨"s", [.lit 3, .lit 1], .floatT, none⟩
        , ⟨"s_prime", [.lit 3, .lit 1], .floatT, none⟩
        , ⟨"F", [.ref "π"], .floatT, none⟩
        , ⟨"o", [.lit 3, .lit 1], .intT, none⟩
        , ⟨"π", [.lit 3], .floatT, none⟩
        , ⟨"u", [.lit 1], .intT, none⟩
        , ⟨"G", [.ref "π"], .floatT, none⟩
        , ⟨"t", [.lit 1], .intT, none⟩ ]
    , .connections
        [ ⟨"D", .directed, "s", none⟩
        , ⟨"s", .undirected, "A", none⟩
        , ⟨"s", .directed, "s_prime", none⟩
        , ⟨"A", .undirected, "o", none⟩
        , ⟨"s", .undirected, "B", none⟩
        , ⟨"C", .directed, "G", none⟩
        , ⟨"E", .directed, "π", none⟩
        , ⟨"G", .directed, "π", none⟩
        , ⟨"π", .directed, "u", none⟩
        , ⟨"B", .directed, "u", none⟩
        , ⟨"u", .directed, "s_prime", none⟩ ]
    , .initialParameterization
        [ ⟨"A", "{(0.9, 0.05, 0.05), (0.05, 0.9, 0.05), (0.05, 0.05, 0.9)}"⟩
        , ⟨"D", "{(0.33333, 0.33333, 0.33333)}"⟩ ]
    , .equations "Standard Active Inference update equations (excerpt)."
    , .time
        [ ⟨"Time", some "t"⟩, ⟨"Dynamic", none⟩, ⟨"Discrete", none⟩
        , ⟨"ModelTimeHorizon", some "Unbounded"⟩ ]
    , .actInfOntologyAnnotation
        [ ⟨"A", "LikelihoodMatrix"⟩, ⟨"s", "HiddenState"⟩
        , ⟨"π", "PolicyVector"⟩, ⟨"G", "ExpectedFreeEnergy"⟩ ]
    , .modelParameters
        [ ⟨"num_hidden_states", "3"⟩, ⟨"num_obs", "3"⟩
        , ⟨"num_actions", "3"⟩, ⟨"num_timesteps", "30"⟩ ]
    , .footer "Active Inference POMDP Agent v1 (excerpt)." ]

/-- Fully observable MDP excerpt (`simple_mdp.md`). -/
def simpleMdpExcerpt : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Simple MDP Agent"
    , .modelAnnotation "Fully observable MDP excerpt"
    , .stateSpaceBlock
        [ ⟨"A", [.lit 4, .lit 4], .floatT, none⟩
        , ⟨"B", [.lit 4, .lit 4, .lit 4], .floatT, none⟩
        , ⟨"C", [.lit 4], .floatT, none⟩
        , ⟨"D", [.lit 4], .floatT, none⟩
        , ⟨"s", [.lit 4, .lit 1], .floatT, none⟩
        , ⟨"s_prime", [.lit 4, .lit 1], .floatT, none⟩
        , ⟨"o", [.lit 4, .lit 1], .intT, none⟩
        , ⟨"π", [.lit 4], .floatT, none⟩
        , ⟨"u", [.lit 1], .intT, none⟩
        , ⟨"G", [.ref "π"], .floatT, none⟩
        , ⟨"t", [.lit 1], .intT, none⟩ ]
    , .connections
        [ ⟨"D", .directed, "s", none⟩
        , ⟨"s", .undirected, "A", none⟩
        , ⟨"s", .directed, "s_prime", none⟩
        , ⟨"A", .undirected, "o", none⟩
        , ⟨"s", .undirected, "B", none⟩
        , ⟨"C", .directed, "G", none⟩
        , ⟨"G", .directed, "π", none⟩
        , ⟨"π", .directed, "u", none⟩
        , ⟨"B", .directed, "u", none⟩
        , ⟨"u", .directed, "s_prime", none⟩ ]
    , .initialParameterization [⟨"A", "{(1.0, 0.0, 0.0, 0.0), ...}"⟩]
    , .equations "Standard Active Inference update equations (excerpt)."
    , .time
        [ ⟨"Time", some "t"⟩, ⟨"Dynamic", none⟩, ⟨"Discrete", none⟩
        , ⟨"ModelTimeHorizon", some "Unbounded"⟩ ]
    , .actInfOntologyAnnotation
        [ ⟨"A", "LikelihoodMatrix"⟩, ⟨"s", "HiddenState"⟩
        , ⟨"u", "Action"⟩, ⟨"t", "Time"⟩ ]
    , .modelParameters
        [ ⟨"num_hidden_states", "4"⟩, ⟨"num_obs", "4"⟩
        , ⟨"num_actions", "4"⟩, ⟨"num_timesteps", "25"⟩ ]
    , .footer "Simple MDP Agent v1 (excerpt)." ]

/-- Closed-loop continuous navigation excerpt
(`continuous_navigation.md`): the linear-Gaussian family with
`goal_mean`/`control_gain` closing the loop. -/
def continuousNavigationExcerpt : GnnDocument where
  sections :=
    [ .gnnSection "ActInfContinuous"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Continuous State Navigation Agent"
    , .modelAnnotation "Closed-loop linear-Gaussian navigator excerpt"
    , .stateSpaceBlock
        [ ⟨"x", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"y", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"u", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"F", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"H", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"Q", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"R", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"prior_mean", [.lit 2], .floatT, none⟩
        , ⟨"prior_cov", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"goal_mean", [.lit 2], .floatT, none⟩
        , ⟨"control_gain", [.lit 1], .floatT, none⟩
        , ⟨"t", [.lit 1], .intT, none⟩ ]
    , .connections
        [ ⟨"prior_mean", .directed, "x", none⟩
        , ⟨"F", .directed, "x", none⟩
        , ⟨"x", .directed, "y", none⟩
        , ⟨"H", .directed, "y", none⟩
        , ⟨"Q", .directed, "x", none⟩
        , ⟨"R", .directed, "y", none⟩
        , ⟨"u", .directed, "x", none⟩
        , ⟨"goal_mean", .directed, "u", none⟩
        , ⟨"control_gain", .directed, "u", none⟩ ]
    , .initialParameterization
        [ ⟨"F", "{(1.0, 0.0), (0.0, 1.0)}"⟩
        , ⟨"prior_mean", "{(0.0, 0.0)}"⟩
        , ⟨"control_gain", "{(0.3)}"⟩ ]
    , .equations "Linear-Gaussian state-space model (excerpt)."
    , .time
        [ ⟨"Time", some "t"⟩, ⟨"Dynamic", none⟩, ⟨"Discrete", none⟩
        , ⟨"ModelTimeHorizon", some "15"⟩ ]
    , .actInfOntologyAnnotation
        [ ⟨"F", "StateTransitionMatrix"⟩, ⟨"H", "ObservationMatrix"⟩
        , ⟨"x", "ContinuousHiddenState"⟩, ⟨"t", "Time"⟩ ]
    , .modelParameters
        [ ⟨"num_timesteps", "15"⟩, ⟨"dt", "0.1"⟩, ⟨"random_seed", "42"⟩
        , ⟨"num_states", "2"⟩, ⟨"num_observations", "2"⟩ ]
    , .footer "Continuous State Navigation Agent v1 (excerpt)."
    , .signature "Cryptographic signature goes here" ]

/-- Passive predictive-coding excerpt (`predictive_coding_agent.md`): the
linear-Gaussian family with no control input. -/
def predictiveCodingExcerpt : GnnDocument where
  sections :=
    [ .gnnSection "ActInfContinuous"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Predictive Coding Active Inference Agent"
    , .modelAnnotation "Passive continuous predictive-coding excerpt"
    , .stateSpaceBlock
        [ ⟨"x", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"y", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"F", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"H", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"Q", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"R", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"prior_mean", [.lit 2], .floatT, none⟩
        , ⟨"prior_cov", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"t", [.lit 1], .intT, none⟩ ]
    , .connections
        [ ⟨"prior_mean", .directed, "x", none⟩
        , ⟨"F", .directed, "x", none⟩
        , ⟨"x", .directed, "y", none⟩
        , ⟨"H", .directed, "y", none⟩
        , ⟨"Q", .directed, "x", none⟩
        , ⟨"R", .directed, "y", none⟩ ]
    , .initialParameterization
        [ ⟨"F", "{(1.0, 0.1), (0.0, 0.8)}"⟩
        , ⟨"prior_cov", "{(1.0, 0.0), (0.0, 1.0)}"⟩ ]
    , .equations "Linear-Gaussian predictive-coding model (excerpt)."
    , .time
        [ ⟨"Time", some "t"⟩, ⟨"Dynamic", none⟩, ⟨"Discrete", none⟩
        , ⟨"ModelTimeHorizon", some "15"⟩ ]
    , .actInfOntologyAnnotation
        [ ⟨"Q", "ProcessNoiseCovariance"⟩, ⟨"x", "ContinuousHiddenState"⟩
        , ⟨"t", "Time"⟩ ]
    , .modelParameters
        [ ⟨"num_timesteps", "15"⟩, ⟨"dt", "0.1"⟩, ⟨"random_seed", "42"⟩ ]
    , .footer "Predictive Coding Active Inference Agent v1 (excerpt)."
    , .signature "Cryptographic signature goes here" ]

/-- v1.1 extension excerpt: a `default=` value hint on a declaration and
annotated connection edges (`:label`), per syntax doc §§2-3. -/
def v11FeatureExcerpt : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1_1 []
    , .modelName "v1.1 feature excerpt"
    , .stateSpaceBlock
        [ ⟨"D", [.lit 3], .floatT, some "uniform"⟩
        , ⟨"A", [.lit 3, .lit 3], .floatT, none⟩
        , ⟨"s", [.lit 3, .lit 1], .floatT, none⟩
        , ⟨"o", [.lit 3, .lit 1], .intT, none⟩ ]
    , .connections
        [ ⟨"D", .directed, "s", some "prior_initialization"⟩
        , ⟨"A", .undirected, "o", some "observation_mapping"⟩ ]
    , .modelParameters [⟨"num_hidden_states", "3"⟩, ⟨"num_obs", "3"⟩]
    , .footer "v1.1 extension excerpt." ]

/-! ## Malformed variants -/

/-- Malformed: the required `Connections` section is absent (GNN-E001). -/
def malformedMissingConnections : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: missing Connections"
    , .stateSpaceBlock [⟨"s", [.lit 3], .floatT, none⟩] ]

/-- Malformed: `Connections` precedes `StateSpaceBlock`, violating the
canonical order. -/
def malformedOutOfOrder : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: out of order"
    , .connections [⟨"s", .directed, "s", none⟩]
    , .stateSpaceBlock [⟨"s", [.lit 3], .floatT, none⟩] ]

/-- Malformed: connection endpoint `X` is not a declared variable
(GNN-E003). -/
def malformedUndeclaredEndpoint : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: undeclared endpoint"
    , .stateSpaceBlock [⟨"s", [.lit 3], .floatT, none⟩]
    , .connections [⟨"X", .directed, "s", none⟩] ]

/-- Malformed: annotation label `likelihood-mapping` contains `-`, outside
the alphanumeric-plus-underscore label grammar. -/
def malformedBadLabel : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: bad label"
    , .stateSpaceBlock
        [ ⟨"s", [.lit 3], .floatT, none⟩
        , ⟨"A", [.lit 3, .lit 3], .floatT, none⟩ ]
    , .connections [⟨"s", .undirected, "A", some "likelihood-mapping"⟩] ]

/-- Malformed: duplicate declaration of `A` (GNN-E004). -/
def malformedDuplicateDecl : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: duplicate declaration"
    , .stateSpaceBlock
        [ ⟨"A", [.lit 3, .lit 3], .floatT, none⟩
        , ⟨"A", [.lit 3, .lit 3], .floatT, none⟩ ]
    , .connections [] ]

/-- Malformed: nonpositive dimension literal `A[0,3]`. -/
def malformedNonpositiveDim : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: nonpositive dimension"
    , .stateSpaceBlock [⟨"A", [.lit 0, .lit 3], .floatT, none⟩]
    , .connections [] ]

/-- Malformed: dimension reference `num_obs` resolves to neither a declared
variable nor a `ModelParameters` key. -/
def malformedUnresolvableDimRef : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: unresolvable dimension reference"
    , .stateSpaceBlock [⟨"A", [.ref "num_obs", .lit 3], .floatT, none⟩]
    , .connections [] ]

/-- Malformed: the `GNNSection` identifier contains a space. -/
def malformedBadSectionId : GnnDocument where
  sections :=
    [ .gnnSection "Act Inf POMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: bad section identifier"
    , .stateSpaceBlock [⟨"s", [.lit 3], .floatT, none⟩]
    , .connections [] ]

/-- Malformed: parameterization of the undeclared variable `Z` (GNN-W003,
strict under the frozen surface). -/
def malformedUndeclaredParamVar : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: undeclared parameterization variable"
    , .stateSpaceBlock [⟨"s", [.lit 3], .floatT, none⟩]
    , .connections []
    , .initialParameterization [⟨"Z", "{(1.0)}"⟩] ]

/-- Malformed: ontology binding for the undeclared variable `q`. -/
def malformedUndeclaredOntologyVar : GnnDocument where
  sections :=
    [ .gnnSection "ActInfPOMDP"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Malformed: undeclared ontology variable"
    , .stateSpaceBlock [⟨"s", [.lit 3], .floatT, none⟩]
    , .connections []
    , .actInfOntologyAnnotation [⟨"q", "HiddenState"⟩] ]

/-! ## Smoke decisions -/

example : documentWellFormed actinfPomdpExcerpt = true := by decide
example : documentWellFormed simpleMdpExcerpt = true := by decide
example : documentWellFormed continuousNavigationExcerpt = true := by decide
example : documentWellFormed predictiveCodingExcerpt = true := by decide
example : documentWellFormed v11FeatureExcerpt = true := by decide

example : ¬WellFormed malformedMissingConnections := by decide
example : ¬WellFormed malformedOutOfOrder := by decide
example : ¬WellFormed malformedUndeclaredEndpoint := by decide
example : ¬WellFormed malformedBadLabel := by decide
example : ¬WellFormed malformedDuplicateDecl := by decide
example : ¬WellFormed malformedNonpositiveDim := by decide
example : ¬WellFormed malformedUnresolvableDimRef := by decide
example : ¬WellFormed malformedBadSectionId := by decide
example : ¬WellFormed malformedUndeclaredParamVar := by decide
example : ¬WellFormed malformedUndeclaredOntologyVar := by decide

end FEP.GnnDocument
