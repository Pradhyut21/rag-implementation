export function formatConfidence(score) {
  if (score === undefined || score === null) return 'N/A';
  return (score * 100).toFixed(1) + '%';
}