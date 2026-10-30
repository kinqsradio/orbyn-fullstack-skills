// Keep startup failures visible even when a module/manifest cannot load.
import('./review.mjs').catch(error => {
  const status = document.getElementById('status');
  status.textContent = `Review unavailable: ${error.message}. No repository save occurred. Existing browser drafts were not erased.`;
  document.body.dataset.reviewReady = 'error';
  for (const node of document.querySelectorAll('button,input,select,textarea')) node.disabled = true;
  const recovery = document.getElementById('recovery');
  let raw = null;
  try { raw = window.localStorage.getItem('export-room-review-v1'); } catch { /* Storage unavailable is not absence of saved work. */ }
  if (raw !== null) {
    recovery.hidden = false; recovery.disabled = false; recovery.textContent = 'Export unvalidated browser recovery';
    recovery.onclick = () => {
      const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' }));
      const link = document.createElement('a'); link.href = url; link.download = 'unvalidated-browser-recovery.json'; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = 'Recovery download requested; validate its source/targets before use. Repository unchanged.';
    };
  }
});
