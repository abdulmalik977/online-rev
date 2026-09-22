// Convenience UI only: real removal requires rebuilding and replacing the host tree.
const cutoff = Date.parse(document.body.dataset.expires + 'T00:00:00Z');
function expirePreview() {
  if (Number.isFinite(cutoff) && Date.now() >= cutoff) {
    document.getElementById('preview-content').hidden = true;
    document.getElementById('expired-message').hidden = false;
  }
}
expirePreview();
setInterval(expirePreview, 60000);
