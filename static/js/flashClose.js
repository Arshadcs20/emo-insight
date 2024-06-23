// JavaScript to handle alert dismissal
document.addEventListener("DOMContentLoaded", function () {
  const closeButtons = document.querySelectorAll(".close");
  closeButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      button.closest(".alert").remove(); // Remove the closest parent element with class 'alert'
    });
  });
});
