document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('.flash-alert');
  alerts.forEach((alert) => {
    setTimeout(() => {
      const instance = bootstrap.Alert.getOrCreateInstance(alert);
      instance.close();
    }, 3500);
  });

  const dateField = document.querySelector('input[type="date"]');
  if (dateField) {
    const today = new Date();
    const iso = today.toISOString().split('T')[0];
    dateField.min = iso;
  }
});