```latex
% ── Page Geometry (tight margins for dense scholarly layout) ──────
\usepackage[margin=1cm, top=1.2cm, bottom=1.2cm, heightrounded]{geometry}

% ── Color Support ─────────────────────────────────────────────────
\usepackage{xcolor}
\definecolor{lean4blue}{RGB}{0,70,150}
\definecolor{mathlibgreen}{RGB}{0,120,60}
\definecolor{fepred}{RGB}{180,30,30}

% ── Mathematics ───────────────────────────────────────────────────
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{mathtools}
\usepackage{amsthm}
\usepackage{bm}

% ── Code Listings ────────────────────────────────────────────────
\usepackage{listings}
\usepackage{fvextra}
\RecustomVerbatimEnvironment{Highlighting}{Verbatim}{
  commandchars=\\\{\},
  breaklines=true,
  breakanywhere=true,
  % Pandoc wraps every token of highlighted code in a \XxxTok macro. Without
  % this, fvextra cannot break inside those macro arguments, so breaklines and
  % breakanywhere are inert for Lean listings and an over-long line runs into
  % the margin instead of wrapping.
  breaknonspaceingroup=true
}
\lstset{
  basicstyle=\ttfamily\footnotesize,
  breaklines=true,
  frame=single,
  captionpos=b,
  numbers=left,
  numberstyle=\tiny,
  keywordstyle=\color{lean4blue}\bfseries,
  commentstyle=\color{gray}\itshape,
  stringstyle=\color{fepred}
}
\lstdefinelanguage{lean4}{
  keywords={theorem,lemma,def,structure,class,instance,variable,import,open,namespace,end,by,exact,rw,apply,simp,linarith,nlinarith,positivity,ring,norm_num,have,show,calc,match,fun,let,where},
  comment=[l]{--},
  morecomment=[s]{/-}{-/},
  string=[b]"
}

% ── Tables & Layout ──────────────────────────────────────────────
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{tabularx}
\usepackage{multirow}

% ── Line-breaking tolerances ─────────────────────────────────────
% Lean identifiers (e.g. ``MeasurableSpace.borel_eq_generateFrom_Ico``) and
% inline code spans frequently break the right margin. Pandoc already
% sets ``\emergencystretch=3em`` and loads ``microtype``; bumping these
% three knobs cuts the overfull-hbox count by roughly a third without
% noticeably increasing interword spacing in normal prose.
\setlength{\emergencystretch}{4em}
\hbadness=2000
\tolerance=4000

% ── Cross-referencing (red hyperlinks: internal, URL, citations) ──
% hyperref is loaded by Pandoc's default template (via bookmark), so
% re-loading it here triggers an option clash. Instead, queue our color
% scheme before the template loads it, and reapply via \hypersetup once
% the document begins (also covers any later override by the template).
\PassOptionsToPackage{colorlinks=true,linkcolor=fepred,urlcolor=fepred,citecolor=fepred,anchorcolor=fepred}{hyperref}
\AtBeginDocument{\hypersetup{colorlinks=true,linkcolor=fepred,urlcolor=fepred,citecolor=fepred,anchorcolor=fepred}}
% Pandoc loads bookmark (and therefore hyperref) after header includes. Queue
% cleveref after bookmark so cross-references are defined in the preamble and
% retain the package ordering required by cleveref.
\AddToHook{package/bookmark/after}{\RequirePackage{cleveref}}
% Headings that name real identifiers (``lean_verifier.py``,
% ``verify_batch(max_workers=1)``, ``FEP_LEAN_VERIFY_VERBOSE=1``) reach
% hyperref's PDF-string sanitizer as a catcode-8 ``_``: Pandoc writes the
% heading as \texorpdfstring{visible}{plain text}, and the plain-text branch
% carries the raw character. hyperref drops every catcode-8 token with
% ``Token not allowed in a PDF string ... removing `subscript'``
% (hyperref.sty:1473), so the visible heading stayed correct while the bookmark
% pane named symbols that do not exist: ``leanverifier.py``,
% ``verifybatch(maxworkers=1)``, ``FEPLEANVERIFYVERBOSE=1``.
%
% \pdfstringdefDisableCommands cannot reach this, because the offending token
% is the bare character rather than \_. The underscore package makes ``_``
% active and, under hyperref's \if@safe@actives, expands it to \string_ --
% a catcode-12 underscore that survives the sanitizer. Math subscripts are
% unaffected (the package routes \ifmmode to \sb) and verbatim is untouched.
\usepackage{underscore}
\AddToHook{package/bookmark/after}{%
  \pdfstringdefDisableCommands{%
    \def\textunderscore{\string_}%
  }%
}

% ── Styled theorem/code panels ───────────────────────────────────
% tcolorbox intentionally NOT loaded: the only style it defined (lean4box)
% is referenced by no manuscript section, and tcolorbox is absent from a
% TeX Live basic install, which aborted every PDF render. Re-add the
% package here together with its first real use, not before.

% ── Theorem environments ─────────────────────────────────────────
\theoremstyle{definition}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{definition}[theorem]{Definition}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{remark}[theorem]{Remark}
\newtheorem{example}[theorem]{Example}

% ── FEP-specific operators ────────────────────────────────────────
\DeclareMathOperator{\KL}{KL}
% G(π) notation for Expected Free Energy, following Parr & Friston (2022)
\DeclareMathOperator{\EFE}{G}
\DeclareMathOperator{\FE}{F}
\DeclareMathOperator{\Ent}{H}
\DeclareMathOperator{\ELBO}{ELBO}
\DeclareMathOperator{\softmax}{softmax}
\newcommand{\E}{\mathbb{E}}
\newcommand{\R}{\mathbb{R}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\Z}{\mathbb{Z}}
\newcommand{\Q}{\mathbb{Q}}
\newcommand{\Prob}{\mathbb{P}}
% Variational free energy with tilde for expected
\newcommand{\VFE}{\widetilde{F}}
% Generative model notation
\newcommand{\gen}[1]{p(#1)}
\newcommand{\rec}[1]{q(#1)}

% Unicode-capable mono font for Lean code listings. Pandoc's Highlighting
% (fancyvrb) environment defaults to \ttfamily = lmtt, which lacks the Greek
% and mathematical glyphs used in the catalogue. FreeSerif covers the complete
% audited prose glyph set.
%
% The code face is JuliaMono, not FreeMono. Lean 4 sources in this catalogue
% use Unicode subscript/superscript operator suffixes (``\circ\_m``, ``\otimes\_m``,
% ``\circ\_k``, ``\forall^m``, ``s^c``, ``\mu\_i``, ``\ldots`` = U+2098 U+2096 U+1D50
% U+209A U+1D62 U+1D9C). FreeMono contains none of them, so XeTeX dropped
% every occurrence silently and printed, among others, the complement lemma
% ``\mu s^c = 1 - \mu s`` as the false statement ``\mu s = 1 - \mu s``. JuliaMono
% is built for exactly this: full Subscripts-and-Superscripts (U+2070-U+209F)
% and Phonetic-Extensions coverage at fixed width. Verify a candidate face with
% ``fc-list ":charset=2098 2096 1D50 209A 1D62 1D9C" family`` before changing it,
% and keep the ``Missing character`` count in the render log at zero.
\usepackage{fontspec}
\setmainfont{FreeSerif}
\setmonofont{JuliaMono}[Scale=MatchLowercase]
\usepackage{ucharclasses}
\newfontfamily\leanunicodefont{FreeSerif}
\setTransitionsFor{MathematicalAlphanumericSymbols}{\leanunicodefont}{}

% Math font for unicode-math: Latin Modern Math has full BMP coverage
% including U+2223 (\mid), U+226A/226B (\ll/\gg), and the Greek/blackboard
% letters used throughout the FEP derivations. Without an explicit
% \setmathfont, unicode-math's fallback chain ends in lmroman text font
% (which lacks U+2223) and warns on every \mid in math mode.
\setmathfont{latinmodern-math.otf}
% ── Legible breaking of long identifiers ──────────────────────────
% The shared template defines \breaktt/\breakseq through seqsplit, whose
% \seqinsert hook is plain stretchable space: a break may fall between ANY two
% characters and leaves no mark. A catalogue table therefore printed
% ``FEP.FiniteKernel.comp_assoc`` as ``FEP.Fini`` / ``teKernel.comp_assoc`` and
% ``FEP.ActiveInference.posteriorState_mul_evidence`` as ``FEP.ActiveI`` /
% ``nference....``, which a reader cannot distinguish from the declaration's
% real spelling. Replace the hook with a discretionary that types a small grey
% continuation arrow at the end of the broken line. The arrow can never be part
% of a Lean name or a Mathlib module path, so the break is unambiguous.
% The cue must be a box: TeX admits only boxes, characters, kerns and rules
% inside a \discretionary, so neither a bare \textcolor (a whatsit) nor an
% inline formula is permitted there. It is typeset once into a box register and
% \copy-ed at each break point, because \seqsplit calls \seqinsert between
% every pair of characters and rebuilding the box would be paid for ~15000
% times per run.
\definecolor{fepbreak}{RGB}{130,130,130}
\newsavebox{\fepbreakbox}
\AtBeginDocument{%
  \savebox{\fepbreakbox}{\normalfont\tiny\textcolor{fepbreak}{\ensuremath{\hookrightarrow}}}}
\def\seqinsert{\ifmmode\allowbreak\else\discretionary{\copy\fepbreakbox}{}{}\fi}

% Code listings wrap under fvextra rather than seqsplit; give them the same cue
% on the continuation line so one document has one break convention.
\fvset{breaksymbolleft={\normalfont\tiny\color{fepbreak}$\hookrightarrow$},breaksymbolsepleft=2pt}

% ── Contents: number columns wide enough for the deepest numbering ─
% secnumdepth is 5 and the appendix numbers reach 15.100, 15.100.1 and
% 5.20.10.1. article's default \@dottedtocline number widths (2.3em / 3.2em /
% 4.1em / 5em) are too narrow for those, so 224 contents lines overflowed their
% number box and printed as ``15.100fep-100'' and ``15.100.1Lean sketch'' with
% the number welded to the title. Widen every level's number box and push each
% level's indent out by its parent's width so the columns still line up.
\makeatletter
\renewcommand*\l@section{\@dottedtocline{1}{0em}{2.6em}}
\renewcommand*\l@subsection{\@dottedtocline{2}{2.6em}{4.3em}}
\renewcommand*\l@subsubsection{\@dottedtocline{3}{6.9em}{5.6em}}
\renewcommand*\l@paragraph{\@dottedtocline{4}{12.5em}{6.4em}}
\renewcommand*\l@subparagraph{\@dottedtocline{5}{18.9em}{7.2em}}
\makeatother

% ── Widows and orphans ────────────────────────────────────────────
% LaTeX's default penalties (150) are low enough that a paragraph may leave a
% single line stranded at the foot or head of a page. In a 347-page document
% with many short paragraphs between headings, that is the most common way a
% page acquires an orphan. These are preventative settings, not a repair of a
% counted defect.
\widowpenalty=10000
\clubpenalty=10000
\displaywidowpenalty=10000
\brokenpenalty=10000

% ── Float placement ───────────────────────────────────────────────
% LaTeX's defaults send a figure to a page of its own as soon as it exceeds
% 70 percent of the text height, which left a float-only page carrying one orphaned
% line of body text. Let a float occupy more of a shared page before a float
% page is opened, and require a float page to be genuinely full.
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.8}
\renewcommand{\textfraction}{0.07}
\renewcommand{\floatpagefraction}{0.8}

% ── Document metadata carried into the PDF /Info dictionary ───────
% manuscript/config.yaml declares a subtitle and a keyword list; pandoc's
% \hypersetup carries only title, author and language, so both were dropped
% from the published PDF. The preamble is copied verbatim by the renderer and
% is never placeholder-substituted, so these two strings are a deliberate copy
% of config.yaml -- ``scripts/render_manuscript.py`` fails closed when they
% drift from it (see pdf_metadata_drift).
\hypersetup{
  pdfsubject={AI-Driven Theorem Sketching and Verification for Active Inference and Bayesian Mechanics},
  pdfkeywords={free energy principle; active inference; bayesian mechanics; lean 4; formal verification; theorem proving; mathlib4; reproducible research; interactive theorem proving; variational inference; information geometry; LLM-ITP integration; execution-integrity pipeline; continuous-time Markov chains; measure theory formalization}}
```
