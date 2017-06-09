$(function () {
  $("#isProxy").change(function() {
    if(this.checked) {
      $('#address').css("display", "table-row")
    } else {
      $('#address').css("display", "none")
    }
  });
});