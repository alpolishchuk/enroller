$(function () {
  $("#isProxy").change(function() {
    if(this.checked) {
      $('#address').css("display", "table-row")
    } else {
      $('#address').css("display", "none")
    }
  });
  $('#authority').change(function () {
    $("select option:selected").each(function() {
      if ($( this ).text() === "Ввести свой адрес УЦ") {
        $('#authoritySelect').css("display", "none")
        $('#authorityText').css("display", "table-row")
      }
    });
  }).change();
});