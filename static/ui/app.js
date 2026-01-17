(function () {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("overlay");
  const openBtn = document.getElementById("sidebarOpen");
  const closeBtn = document.getElementById("sidebarClose");

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("open");
    if (overlay) overlay.classList.add("open");
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("open");
    if (overlay) overlay.classList.remove("open");
  }

  if (openBtn) openBtn.addEventListener("click", openSidebar);
  if (closeBtn) closeBtn.addEventListener("click", closeSidebar);
  if (overlay) overlay.addEventListener("click", closeSidebar);

  // Optional: subtle “tap” animation on buttons
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("button, a.btn, .nav-item, .icon-btn");
    if (!btn) return;
    btn.classList.add("tap");
    setTimeout(() => btn.classList.remove("tap"), 160);
  });
})();
