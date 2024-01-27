document.addEventListener("DOMContentLoaded", function() {
    const menuItems = document.querySelectorAll(".side-menu li");

    menuItems.forEach(function(item) {
        item.addEventListener("click", function() {
            // Remove 'active' class from all menu items
            menuItems.forEach(function(item) {
                item.classList.remove("active");
            });

            // Add 'active' class to the parent 'li' of the clicked 'a' element
            this.classList.add("active");
        });
    });
});
