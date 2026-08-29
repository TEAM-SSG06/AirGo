// Helper utilities (currency formatting, date calculations, DGCA weights, chart helpers)
export const formatCurrency = (val) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(val);
};

export const formatPercent = (val) => {
  const prefix = val > 0 ? '+' : '';
  return `${prefix}${val.toFixed(2)}%`;
};
