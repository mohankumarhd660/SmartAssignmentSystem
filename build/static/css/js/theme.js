// theme.js
const toggle = document.getElementById("theme-toggle");
const root = document.documentElement;

toggle.addEventListener("click", () => {
  const isDark = root.classList.toggle("dark-mode");
  localStorage.setItem("dark-mode", isDark);
});

if (localStorage.getItem("dark-mode") === "true") {
  root.classList.add("dark-mode");
}
