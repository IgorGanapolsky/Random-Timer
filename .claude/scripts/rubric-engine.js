/**
 * Rubric-Based Reward Engine
 *
 * Composable rubric evaluation framework for RL reward signals.
 * Replaces scalar scoring with structured, multi-dimensional rubrics.
 *
 * Inspired by Cameron Wolfe's "Rubric-Based Rewards for RL" overview:
 * - Dimensions with independent criteria and weights
 * - Score normalization to 0-1 range
 * - Support for non-verifiable domains (subjective evaluation)
 *
 * @see .claude/scripts/evaluate-memory.js — predecessor (scalar scoring)
 * @see .claude/scripts/feedback/capture-feedback.js — binary feedback
 */

// ---------------------------------------------------------------------------
// Built-in Rubric Definitions
// ---------------------------------------------------------------------------

const MEMORY_QUALITY_RUBRIC = {
  name: 'memory-quality',
  version: '1.0.0',
  description: 'Evaluate stored memory quality for RL reward shaping',
  dimensions: [
    {
      name: 'actionability',
      description: 'Can the memory be directly applied to solve problems?',
      weight: 0.25,
      scale: { min: 1, max: 5 },
      nonVerifiable: false,
      criteria: [
        { score: 1, description: 'No actionable content' },
        { score: 2, description: 'Vague suggestions without concrete steps' },
        { score: 3, description: 'Some actionable steps but missing context' },
        { score: 4, description: 'Clear steps with partial context' },
        { score: 5, description: 'Clear, directly applicable steps with context' },
      ],
    },
    {
      name: 'specificity',
      description: 'Does it reference concrete files, commands, error messages?',
      weight: 0.2,
      scale: { min: 1, max: 5 },
      nonVerifiable: false,
      criteria: [
        { score: 1, description: 'Entirely generic, no concrete references' },
        { score: 2, description: 'Mentions concepts but no specific artifacts' },
        { score: 3, description: 'Some file paths or commands referenced' },
        { score: 4, description: 'Multiple specific references with context' },
        { score: 5, description: 'Exact files, line numbers, commands, and error messages' },
      ],
    },
    {
      name: 'freshness',
      description: 'Is the information current and not outdated?',
      weight: 0.2,
      scale: { min: 1, max: 5 },
      nonVerifiable: true,
      criteria: [
        { score: 1, description: 'Outdated or deprecated information' },
        { score: 2, description: 'Possibly outdated, no date indicators' },
        { score: 3, description: 'Moderately current, some parts may be stale' },
        { score: 4, description: 'Recent and mostly current' },
        { score: 5, description: 'Up-to-date with latest project state' },
      ],
    },
    {
      name: 'completeness',
      description: 'Does it provide full context (cause, solution, verification)?',
      weight: 0.2,
      scale: { min: 1, max: 5 },
      nonVerifiable: false,
      criteria: [
        { score: 1, description: 'Fragment with no context' },
        { score: 2, description: 'Partial information, missing key details' },
        { score: 3, description: 'Covers main points but lacks verification steps' },
        { score: 4, description: 'Cause and solution present, verification implied' },
        { score: 5, description: 'Full cause, solution, and verification steps' },
      ],
    },
    {
      name: 'uniqueness',
      description: 'Does it capture knowledge not easily found elsewhere?',
      weight: 0.15,
      scale: { min: 1, max: 5 },
      nonVerifiable: true,
      criteria: [
        { score: 1, description: 'Easily found in documentation or Stack Overflow' },
        { score: 2, description: 'Common knowledge with minor project context' },
        { score: 3, description: 'Mix of standard and project-specific knowledge' },
        { score: 4, description: 'Mostly project-specific tribal knowledge' },
        { score: 5, description: 'Unique insight only discoverable through experience' },
      ],
    },
  ],
};

const CODE_REVIEW_RUBRIC = {
  name: 'code-review',
  version: '1.0.0',
  description: 'Evaluate code changes for review quality signals',
  dimensions: [
    {
      name: 'correctness',
      description: 'Does the code work as intended?',
      weight: 0.3,
      scale: { min: 1, max: 5 },
      nonVerifiable: false,
      criteria: [
        { score: 1, description: 'Broken — does not compile or crashes at runtime' },
        { score: 2, description: 'Partially works but has significant bugs' },
        { score: 3, description: 'Works for happy path, edge cases not handled' },
        { score: 4, description: 'Works correctly with minor edge case gaps' },
        { score: 5, description: 'Fully correct with edge cases handled' },
      ],
    },
    {
      name: 'security',
      description: 'Are there security concerns?',
      weight: 0.25,
      scale: { min: 1, max: 5 },
      nonVerifiable: false,
      criteria: [
        { score: 1, description: 'Critical vulnerability (secrets exposed, injection)' },
        { score: 2, description: 'Significant security concern' },
        { score: 3, description: 'Minor security concern, low risk' },
        { score: 4, description: 'No obvious concerns, follows standard practices' },
        { score: 5, description: 'Explicitly addresses security with validation/sanitization' },
      ],
    },
    {
      name: 'maintainability',
      description: 'Is the code readable and well-structured?',
      weight: 0.2,
      scale: { min: 1, max: 5 },
      nonVerifiable: true,
      criteria: [
        { score: 1, description: 'Unreadable, no structure, magic values everywhere' },
        { score: 2, description: 'Difficult to follow, poor naming' },
        { score: 3, description: 'Readable but could be cleaner' },
        { score: 4, description: 'Clean, well-named, follows conventions' },
        { score: 5, description: 'Exemplary — clear intent, good abstractions' },
      ],
    },
    {
      name: 'testCoverage',
      description: 'Are critical paths tested?',
      weight: 0.15,
      scale: { min: 1, max: 5 },
      nonVerifiable: false,
      criteria: [
        { score: 1, description: 'No tests at all' },
        { score: 2, description: 'Minimal tests, critical paths untested' },
        { score: 3, description: 'Happy path tested, edge cases missing' },
        { score: 4, description: 'Good coverage of main scenarios' },
        { score: 5, description: 'Comprehensive tests including edge cases' },
      ],
    },
    {
      name: 'performance',
      description: 'Are there performance concerns?',
      weight: 0.1,
      scale: { min: 1, max: 5 },
      nonVerifiable: true,
      criteria: [
        { score: 1, description: 'Severe performance issue (O(n²) in hot path, memory leak)' },
        { score: 2, description: 'Notable performance concern' },
        { score: 3, description: 'Acceptable, no obvious bottlenecks' },
        { score: 4, description: 'Good performance characteristics' },
        { score: 5, description: 'Optimized with performance considerations documented' },
      ],
    },
  ],
};

const AGENT_PERFORMANCE_RUBRIC = {
  name: 'agent-performance',
  version: '1.0.0',
  description: 'Evaluate AI agent task execution quality',
  dimensions: [
    {
      name: 'taskCompletion',
      description: 'Did the agent complete the requested task?',
      weight: 0.3,
      scale: { min: 1, max: 5 },
      nonVerifiable: false,
      criteria: [
        { score: 1, description: 'Task not attempted or completely wrong' },
        { score: 2, description: 'Partial attempt, major requirements missed' },
        { score: 3, description: 'Core task done but secondary requirements missed' },
        { score: 4, description: 'Task completed with minor gaps' },
        { score: 5, description: 'All requirements fully satisfied' },
      ],
    },
    {
      name: 'minimalDiff',
      description: 'Did it touch only necessary code?',
      weight: 0.2,
      scale: { min: 1, max: 5 },
      nonVerifiable: false,
      criteria: [
        { score: 1, description: 'Rewrote unrelated files, massive unnecessary changes' },
        { score: 2, description: 'Significant unrelated changes mixed in' },
        { score: 3, description: 'Some unnecessary changes but mostly focused' },
        { score: 4, description: 'Tight diff with minor extra touches' },
        { score: 5, description: 'Surgical — only necessary lines changed' },
      ],
    },
    {
      name: 'conventionAdherence',
      description: 'Did it follow project patterns?',
      weight: 0.2,
      scale: { min: 1, max: 5 },
      nonVerifiable: true,
      criteria: [
        { score: 1, description: 'Ignored all project conventions' },
        { score: 2, description: 'Some conventions followed, major violations' },
        { score: 3, description: 'Mostly follows conventions with notable gaps' },
        { score: 4, description: 'Consistent with project patterns' },
        { score: 5, description: 'Perfectly matches existing style and patterns' },
      ],
    },
    {
      name: 'verification',
      description: 'Did it verify its work (run tests, check output)?',
      weight: 0.15,
      scale: { min: 1, max: 5 },
      nonVerifiable: false,
      criteria: [
        { score: 1, description: 'No verification at all' },
        { score: 2, description: 'Claimed success without evidence' },
        { score: 3, description: 'Basic verification (syntax check only)' },
        { score: 4, description: 'Ran tests and checked output' },
        { score: 5, description: 'Full verification with evidence (logs, diffs, test output)' },
      ],
    },
    {
      name: 'communication',
      description: 'Was the response clear and appropriately concise?',
      weight: 0.15,
      scale: { min: 1, max: 5 },
      nonVerifiable: true,
      criteria: [
        { score: 1, description: 'Incomprehensible or massively over-explained' },
        { score: 2, description: 'Confusing or unnecessarily verbose' },
        { score: 3, description: 'Understandable but could be more concise' },
        { score: 4, description: 'Clear and well-structured response' },
        { score: 5, description: 'Concise, precise, and well-organized' },
      ],
    },
  ],
};

// ---------------------------------------------------------------------------
// Core Functions
// ---------------------------------------------------------------------------

/**
 * Validate and create a rubric from a definition object.
 *
 * @param {object} definition - Rubric definition
 * @returns {object} Frozen rubric object
 * @throws {Error} On invalid definition
 */
function createRubric(definition) {
  if (!definition || typeof definition !== 'object') {
    throw new Error('Rubric definition must be a non-null object');
  }

  if (!definition.name || typeof definition.name !== 'string') {
    throw new Error('Rubric must have a string "name"');
  }

  if (!definition.version || typeof definition.version !== 'string') {
    throw new Error('Rubric must have a string "version"');
  }

  if (!Array.isArray(definition.dimensions) || definition.dimensions.length === 0) {
    throw new Error('Rubric must have a non-empty "dimensions" array');
  }

  const seenNames = new Set();

  for (const dim of definition.dimensions) {
    if (!dim.name || typeof dim.name !== 'string') {
      throw new Error('Each dimension must have a string "name"');
    }

    if (seenNames.has(dim.name)) {
      throw new Error(`Duplicate dimension name: "${dim.name}"`);
    }
    seenNames.add(dim.name);

    if (typeof dim.weight !== 'number' || dim.weight < 0 || dim.weight > 1) {
      throw new Error(`Dimension "${dim.name}" weight must be a number between 0 and 1`);
    }

    if (
      !dim.scale ||
      typeof dim.scale.min !== 'number' ||
      typeof dim.scale.max !== 'number' ||
      dim.scale.min >= dim.scale.max
    ) {
      throw new Error(`Dimension "${dim.name}" must have a valid scale with min < max`);
    }

    if (!Array.isArray(dim.criteria) || dim.criteria.length === 0) {
      throw new Error(`Dimension "${dim.name}" must have a non-empty "criteria" array`);
    }
  }

  // Validate weights sum to ~1.0 (allow floating point tolerance)
  const weightSum = definition.dimensions.reduce((sum, d) => sum + d.weight, 0);
  if (Math.abs(weightSum - 1.0) > 0.001) {
    throw new Error(
      `Dimension weights must sum to 1.0, got ${weightSum.toFixed(4)}`
    );
  }

  return Object.freeze({ ...definition });
}

/**
 * Normalize a raw score to the 0-1 range given a scale.
 *
 * @param {number} rawScore - The raw score value
 * @param {{ min: number, max: number }} scale - The scale definition
 * @returns {number} Normalized score between 0 and 1
 */
function normalizeScore(rawScore, scale) {
  if (typeof rawScore !== 'number' || typeof scale.min !== 'number' || typeof scale.max !== 'number') {
    throw new Error('rawScore, scale.min, and scale.max must be numbers');
  }

  if (scale.min >= scale.max) {
    throw new Error('scale.min must be less than scale.max');
  }

  // Clamp to scale bounds before normalizing
  const clamped = Math.max(scale.min, Math.min(scale.max, rawScore));
  return (clamped - scale.min) / (scale.max - scale.min);
}

/**
 * Validate that scores object matches the rubric dimensions.
 *
 * @param {object} rubric - A rubric created via createRubric
 * @param {object} scores - Map of dimension name → raw score
 * @returns {{ valid: boolean, errors: string[] }}
 */
function validateScores(rubric, scores) {
  const errors = [];

  if (!scores || typeof scores !== 'object') {
    return { valid: false, errors: ['Scores must be a non-null object'] };
  }

  for (const dim of rubric.dimensions) {
    if (!(dim.name in scores)) {
      errors.push(`Missing score for dimension "${dim.name}"`);
      continue;
    }

    const score = scores[dim.name];

    if (typeof score !== 'number') {
      errors.push(`Score for "${dim.name}" must be a number, got ${typeof score}`);
      continue;
    }

    if (score < dim.scale.min || score > dim.scale.max) {
      errors.push(
        `Score for "${dim.name}" is ${score}, must be between ${dim.scale.min} and ${dim.scale.max}`
      );
    }
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Evaluate scores against a rubric and produce a weighted aggregate.
 *
 * @param {object} rubric - A rubric created via createRubric
 * @param {object} scores - Map of dimension name → raw score
 * @returns {{ aggregate: number, dimensions: object[], nonVerifiableWeight: number }}
 */
function evaluateWithRubric(rubric, scores) {
  const validation = validateScores(rubric, scores);
  if (!validation.valid) {
    throw new Error(`Invalid scores: ${validation.errors.join('; ')}`);
  }

  let aggregate = 0;
  let nonVerifiableWeight = 0;
  const dimensionResults = [];

  for (const dim of rubric.dimensions) {
    const rawScore = scores[dim.name];
    const normalized = normalizeScore(rawScore, dim.scale);
    const weighted = normalized * dim.weight;

    aggregate += weighted;

    if (dim.nonVerifiable) {
      nonVerifiableWeight += dim.weight;
    }

    dimensionResults.push({
      name: dim.name,
      rawScore,
      normalizedScore: normalized,
      weightedScore: weighted,
      weight: dim.weight,
      nonVerifiable: !!dim.nonVerifiable,
    });
  }

  return {
    aggregate,
    dimensions: dimensionResults,
    nonVerifiableWeight,
  };
}

/**
 * Format a human-readable rubric evaluation report.
 *
 * @param {object} rubric - The rubric definition
 * @param {object} scores - Map of dimension name → raw score
 * @param {{ aggregate: number, dimensions: object[], nonVerifiableWeight: number }} result
 * @returns {string}
 */
function formatRubricReport(rubric, scores, result) {
  const lines = [];

  lines.push(`Rubric: ${rubric.name} v${rubric.version}`);
  if (rubric.description) {
    lines.push(rubric.description);
  }
  lines.push('─'.repeat(50));

  for (const dimResult of result.dimensions) {
    const dim = rubric.dimensions.find((d) => d.name === dimResult.name);
    const nv = dimResult.nonVerifiable ? ' [non-verifiable]' : '';
    const pct = (dimResult.weight * 100).toFixed(0);

    lines.push(
      `${dimResult.name} (${pct}%): ${dimResult.rawScore}/${dim.scale.max} → ${dimResult.normalizedScore.toFixed(2)}${nv}`
    );

    // Find matching criteria description
    const matchedCriteria = dim.criteria
      .slice()
      .sort((a, b) => Math.abs(a.score - dimResult.rawScore) - Math.abs(b.score - dimResult.rawScore))[0];

    if (matchedCriteria) {
      lines.push(`  → ${matchedCriteria.description}`);
    }
  }

  lines.push('─'.repeat(50));
  lines.push(`Aggregate Score: ${result.aggregate.toFixed(3)} / 1.000`);

  if (result.nonVerifiableWeight > 0) {
    lines.push(
      `Non-verifiable weight: ${(result.nonVerifiableWeight * 100).toFixed(0)}% (subjective dimensions)`
    );
  }

  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  // Core functions
  createRubric,
  normalizeScore,
  validateScores,
  evaluateWithRubric,
  formatRubricReport,

  // Built-in rubric definitions
  MEMORY_QUALITY_RUBRIC,
  CODE_REVIEW_RUBRIC,
  AGENT_PERFORMANCE_RUBRIC,
};
