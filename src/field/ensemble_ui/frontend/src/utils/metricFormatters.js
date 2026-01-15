/**
 * Utility functions for formatting agent execution metrics
 */

/**
 * Format duration from milliseconds to human-readable string
 * @param {number|null|undefined} durationMs - Duration in milliseconds
 * @returns {string} Formatted duration string
 */
export function formatDuration(durationMs) {
  if (durationMs === null || durationMs === undefined) {
    return '-';
  }

  if (durationMs < 1000) {
    return `${durationMs}ms`;
  }

  const seconds = Math.floor(durationMs / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

/**
 * Format cost to display with appropriate decimal places
 * @param {number|null|undefined} cost - Cost in dollars
 * @returns {string} Formatted cost string
 */
export function formatCost(cost) {
  if (cost === null || cost === undefined) {
    return '-';
  }

  if (cost === 0) {
    return '$0.00';
  }

  if (cost < 0.01) {
    return `$${cost.toFixed(4)}`;
  }

  if (cost < 1) {
    return `$${cost.toFixed(3)}`;
  }

  return `$${cost.toFixed(2)}`;
}

/**
 * Get color class based on cost tier
 * @param {number|null|undefined} cost - Cost in dollars
 * @returns {string} Tailwind CSS color class
 */
export function getCostColorClass(cost) {
  if (cost === null || cost === undefined) {
    return 'text-gray-400';
  }

  if (cost < 0.01) {
    return 'text-green-300';
  }

  if (cost < 0.10) {
    return 'text-yellow-300';
  }

  if (cost < 1.00) {
    return 'text-orange-300';
  }

  return 'text-red-300';
}

/**
 * Shorten full model name for display
 * @param {string|null|undefined} model - Full model identifier
 * @returns {string} Shortened model name
 */
export function formatModelName(model) {
  if (!model || model === 'unknown') {
    return '-';
  }

  // Common model name mappings
  const modelMappings = {
    'claude-3-5-haiku-latest': 'Haiku',
    'claude-3-5-sonnet-latest': 'Sonnet',
    'claude-3-opus-latest': 'Opus',
    'claude-3-5-haiku-20241022': 'Haiku',
    'claude-3-5-sonnet-20241022': 'Sonnet',
    'claude-3-opus-20240229': 'Opus',
    'claude-opus-4-5-20251101': 'Opus 4.5',
    'claude-sonnet-4-20250514': 'Sonnet 4',
  };

  if (modelMappings[model]) {
    return modelMappings[model];
  }

  // Fallback: extract key part from model name
  if (model.includes('haiku')) return 'Haiku';
  if (model.includes('sonnet')) return 'Sonnet';
  if (model.includes('opus')) return 'Opus';

  // Return shortened version if too long
  if (model.length > 15) {
    return model.substring(0, 12) + '...';
  }

  return model;
}

/**
 * Get model tier color class
 * @param {string|null|undefined} model - Model identifier
 * @returns {string} Tailwind CSS color class
 */
export function getModelColorClass(model) {
  if (!model) {
    return 'bg-gray-500/30 text-gray-300';
  }

  const modelLower = model.toLowerCase();

  if (modelLower.includes('opus')) {
    return 'bg-purple-500/30 text-purple-200';
  }

  if (modelLower.includes('sonnet')) {
    return 'bg-blue-500/30 text-blue-200';
  }

  if (modelLower.includes('haiku')) {
    return 'bg-green-500/30 text-green-200';
  }

  return 'bg-gray-500/30 text-gray-300';
}

/**
 * Format token count for display
 * @param {number|null|undefined} tokens - Number of tokens
 * @returns {string} Formatted token count
 */
export function formatTokens(tokens) {
  if (tokens === null || tokens === undefined) {
    return '-';
  }

  if (tokens < 1000) {
    return tokens.toString();
  }

  if (tokens < 1000000) {
    return `${(tokens / 1000).toFixed(1)}K`;
  }

  return `${(tokens / 1000000).toFixed(2)}M`;
}
