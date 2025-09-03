// script.js
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("clickBtn");
  const output = document.getElementById("output");

  btn.addEventListener("click", () => {
    const now = new Date();
    output.textContent = `आपने बटन ${now.toLocaleTimeString()} पर क्लिक किया!`;
  });
});
