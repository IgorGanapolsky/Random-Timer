'use strict';
/**
 * Rubric Engine — Agent Performance Evaluation
 *
 * Scores agent behavior across 5 weighted dimensions (0.0–1.0 each).
 * Used by capture-feedback.js for rubric-based RLHF signal enrichment.
 *
 * Exports:
 *   DIMENSIONS            — dimension definitions with weights
 *   AGENT_PERFORMANCE_RUBRIC — alias for DIMENSIONS (used by capture-feedback.js)
 *   evaluate(context)     — evaluate from a rich context object
 *   evaluateWithRubric(rubric, scores) — evaluate raw scores against a rubric
 *   formatRubricReport(rubric, scores, result) — format a human-readable report
 *   gradeFromScore(score) — map 0-1 score to letter grade
 */

// ---------------------------------------------------------------------------
// Dimension definitions
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} Dimension
 * @property {string} name        - Machine-friendly key
 * @property {string} label       - Human-readable label
 * @property {number} weight      - Contribution to totalScore (weights sum to 1.0)
 * @property {string} description - What is being measured
 * @property {Object} anchors     - Score anchors: 1.0 / 0.5 / 0.0 examples
 */

/** @type {Dimension[]} */
const DIMENSIONS = [
  {
    name: 'taskCompletion',
    label: 'Task Completion',
    weight: 0.30,
    description: 'Did the task complete successfully?',
    anchors: {
      1.0: 'Fully completed with all acceptance criteria met',
      0.5: 'Partially completed — core done but edge cases or follow-ups missing',
      0.0: 'Task failed or not attempted',
    },
  },
  {
    name: 'minimalDiff',
    label: 'Minimal Diff',
    weight: 0.20,
    description: 'Were changes minimal and focused?',
    anchors: {
      1.0: 'Surgical — only the necessary lines changed',
      0.5: 'Some bloat — minor unrelated changes included',
      0.0: 'Massive unnecessary changes; high noise-to-signal ratio',
    },
  },
  {
    name: 'conventionAdherence',
    label: 'Convention Adherence',
    weight: 0.15,
    description: 'Followed project conventions?',
    anchors: {
      1.0: 'Perfect — naming, style, commit format, exports all correct',
      0.5: 'Minor deviation from conventions',
      0.0: 'Violated conventions (wrong exports, bad commits, style ignored)',
    },
  },
  {
    name: 'verification',
    label: 'Verification',
    weight: 0.20,
    description: 'Did the agent verify before claiming done?',
    anchors: {
      1.0: 'Tested and verified — build, tests, or e2e confirmed passing',
      0.5: 'Partial check — inspected files but did not run tests',
      0.0: 'Claimed done without any verification',
    },
  },
  {
    name: 'communication',
    label: 'Communication',
    weight: 0.15,
    description: 'Clear, concise, honest communication?',
    anchors: {
      1.0: 'Excellent — direct, accurate, evidence-backed, no padding',
      0.5: 'Acceptable — mostly clear but some verbosity or hedging',
      0.0: 'Lied, misleading, verbose, or unclear',
    },
  },
];

// Weights must sum to 1.0 — enforce at load time.
const _weightSum = DIMENSIONS.reduce((s, d) => s + d.weight, 0);
if (Math.abs(_weightSum - 1.0) > 0.0001) {
  throw new Error(`rubric-engine: DIMENSIONS weights sum to ${_weightSum}, expected 1.0`);
}

/**
 * AGENT_PERFORMANCE_RUBRIC is the canonical export consumed by capture-feedback.js.
 * It is intentionally the same object as DIMENSIONS.
 */
const AGENT_PERFORMANCE_RUBRIC = DIMENSIONS;

// ---------------------------------------------------------------------------
// Grade mapping
// ---------------------------------------------------------------------------

/**
 * Map a 0-1 aggregate score to a letter grade.
 * @param {number} score - 0.0 to 1.0
 * @returns {'A'|'B'|'C'|'D'|'F'}
 */
function gradeFromScore(score) {
  if (score >= 0.9) return 'A';
  if (score >= 0.75) return 'B';
  if (score >= 0.6) return 'C';
  if (score >= 0.4) return 'D';
  return 'F';
}

// ---------------------------------------------------------------------------
// Core evaluation
// ---------------------------------------------------------------------------

/**
 * Evaluate raw dimension scores against a rubric definition.
 *
 * capture-feedback.js calls this as:
 *   evaluateWithRubric(AGENT_PERFORMANCE_RUBRIC, scores)
 * where `scores` is a plain object keyed by dimension name, values are
 * numeric scores on any scale — we normalise to 0-1 by dividing by 5
 * when values are clearly on a 0-5 scale, otherwise clamp to 0-1.
 *
 * @param {Dimension[]} rubric - array of dimension definitions
 * @param {Object} scores      - { dimensionName: number, ... }
 * @returns {{ dimensions: Object, aggregate: number, grade: string }}
 */
function evaluateWithRubric(rubric, scores) {
  const dimensionResults = {};
  let weightedSum = 0;
  let totalWeight = 0;

  rubric.forEach(dim => {
    const raw = scores[dim.name];
    if (raw === undefined || raw === null) {
      // Missing dimension — treat as 0 (no credit)
      dimensionResults[dim.name] = 0;
    } else {
      // Detect 0-5 scale: if any score > 1, normalise the whole set
      const normalised = _normaliseScore(raw);
      dimensionResults[dim.name] = normalised;
      weightedSum += normalised * dim.weight;
    }
    totalWeight += dim.weight;
  });

  // Guard against all-missing input
  const aggregate = totalWeight > 0 ? weightedSum / totalWeight : 0;
  const grade = gradeFromScore(aggregate);

  return { dimensions: dimensionResults, aggregate, grade };
}

/**
 * Evaluate from a rich context object (spec-required `evaluate` export).
 *
 * @param {Object} context
 * @param {string}  context.task      - Task description
 * @param {string[]} [context.actions] - Actions taken
 * @param {string}  [context.outcome] - Outcome description
 * @param {string}  [context.feedback] - Freeform feedback
 * @param {Object}  [context.scores]  - Optional explicit dimension scores
 * @returns {{ dimensions: Object, totalScore: number, grade: string }}
 */
function evaluate(context) {
  const { scores = {} } = context || {};

  // If explicit scores are provided, delegate to evaluateWithRubric
  const result = evaluateWithRubric(DIMENSIONS, scores);

  return {
    dimensions: result.dimensions,
    totalScore: result.aggregate,
    grade: result.grade,
  };
}

// ---------------------------------------------------------------------------
// Report formatting
// ---------------------------------------------------------------------------

/**
 * Format a human-readable rubric report string.
 *
 * capture-feedback.js calls this as:
 *   formatRubricReport(AGENT_PERFORMANCE_RUBRIC, scores, result)
 *
 * @param {Dimension[]} rubric
 * @param {Object} scores  - raw input scores
 * @param {{ dimensions: Object, aggregate: number, grade: string }} result
 * @returns {string}
 */
function formatRubricReport(rubric, scores, result) {
  const lines = [
    'Agent Performance Rubric Report',
    '================================',
  ];

  rubric.forEach(dim => {
    const normalised = result.dimensions[dim.name] !== undefined
      ? result.dimensions[dim.name]
      : 0;
    const raw = scores[dim.name] !== undefined ? scores[dim.name] : 'n/a';
    const bar = _progressBar(normalised, 10);
    lines.push(
      `${dim.label.padEnd(22)} [${bar}] ${(normalised * 100).toFixed(0).padStart(3)}%` +
      `  (raw: ${raw}, weight: ${(dim.weight * 100).toFixed(0)}%)`
    );
  });

  lines.push('--------------------------------');
  lines.push(
    `Aggregate Score: ${result.aggregate.toFixed(3)}  |  Grade: ${result.grade}`
  );

  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Normalise a raw score to 0-1.
 * Supports 0-1 and 0-5 scales; clamps to [0, 1].
 * @param {number} raw
 * @returns {number}
 */
function _normaliseScore(raw) {
  if (raw > 1) {
    // Assume 0-5 scale
    return Math.min(1, Math.max(0, raw / 5));
  }
  return Math.min(1, Math.max(0, raw));
}

/**
 * Build a simple ASCII progress bar.
 * @param {number} ratio  - 0-1
 * @param {number} width  - total bar characters
 * @returns {string}
 */
function _progressBar(ratio, width) {
  const filled = Math.round(ratio * width);
  return '\u2588'.repeat(filled) + '\u2591'.repeat(width - filled);
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  DIMENSIONS,
  AGENT_PERFORMANCE_RUBRIC,
  evaluate,
  evaluateWithRubric,
  formatRubricReport,
  gradeFromScore,
};
