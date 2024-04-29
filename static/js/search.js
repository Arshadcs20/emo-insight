$(document).ready(function () {
  $("#searchInput").on("keyup", function () {
    var value = $(this).val().toLowerCase();
    $(".item").each(function () {
      var title = $(this).find(".title").text().toLowerCase();
      var videoUrl = $(this).find(".video-url").text().toLowerCase();
      var confidenceLevel = $(this)
        .find(".confidence-level")
        .text()
        .toLowerCase();
      var transcription = $(this).find(".transcription").text().toLowerCase();

      var matchFound = false;

      // Check if the value is found in any of the fields
      if (
        title.indexOf(value) > -1 ||
        videoUrl.indexOf(value) > -1 ||
        confidenceLevel.indexOf(value) > -1 ||
        transcription.indexOf(value) > -1
      ) {
        matchFound = true;
      }

      if (matchFound) {
        // Highlight the matching text
        $(this)
          .find(".title, .video-url, .confidence-level, .transcription")
          .each(function () {
            var text = $(this).text();
            var regex = new RegExp("(" + value + ")", "gi");
            var newText = text.replace(
              regex,
              '<span class="highlight">$1</span>'
            );
            $(this).html(newText);
          });
        $(this).show();
      } else {
        // If no match, hide the element
        $(this).hide();
      }
    });
  });
});
