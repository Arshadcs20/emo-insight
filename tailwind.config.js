// tailwind.config.js

module.exports = {
  content: [
    "./templates/**/*.html", // Adjust the path to your HTML templates
    "./templates/*.html",
    "./static/**/*.js", // Adjust the path to your JS files
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
//npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch
