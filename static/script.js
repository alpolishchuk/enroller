$(function () {
  $("#isProxy").change(function() {
    if(this.checked) {
      $('#address').css("display", "table-row")
    } else {
      $('#address').css("display", "none")
    }
  });
  $('#authority').change(function () {
    if ($( "#authority option:selected" ).text() === "Ввести свой адрес УЦ") {
      $('#authority_text').css("display", "table-row")
    } else {
      $('#authority_text').css("display", "none")
    }
  }).change();
  $('#certform').validate({
    rules: {
      proxy_address: {
        required: $('#address:checked')
      },
      proxy_port: {
        digits: true,
        maxlength: 5,
        required: $('#address:checked')
      },
      authority_text: {
        required: true
      }
    },
    messages: {
      request: "*",
      proxy_address: "*",
      authority_text: "*",
      proxy_port: {
        digits: "Некорректный порт",
        maxlength: "Значение порта не должно превышать 65535",
        required: "*"
      }
    },
    errorPlacement: function(error, element) {
      error.insertAfter(element)
      error.addClass('message');  // add a class to the wrapper
      error.css('margin-left', 5);
      error.css('border', 'none');
      error.css('color', 'red');
      $('#required').css('display', 'block').css('margin', '10px auto auto 25px');
    }
  })
});