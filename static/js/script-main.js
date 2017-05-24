// Main File with Javascript functionality

  //Submit data when enter key is pressed
  $('#input_frase_arg').keydown(function(e) {
      var text = $('#input_frase_arg').val();
        if (e.which == 13 && text.length > 0) { //catch Enter key
          //POST request to API to create a new visitor entry in the database
            analyze_text(text);
        }
    });

  //Submit data when enter key is pressed
  $('#input_imagen_arg').keydown(function(e) {
      var text = $('#input_imagen_arg').val();
        if (e.which == 13 && text.length > 0) { //catch Enter key
          //POST request to API to create a new visitor entry in the database
            analyze_image(text);
        }
    });

    function analyze_text(text){
      $.ajax({
          method: "POST",
          url: "./api/analyze-text",
          contentType: "application/json",
          data: JSON.stringify({text: text })
        })
      .done(function(data) {
          // $('#input_frase').hide();
          // $('#input_imagen_all').hide();
          $('#banner-fig').hide();
          $('#input_frase_arg').val("");
          $('#response').html(data);
          getHistory();
      });
    };



    function analyze_image(text){

      $.ajax({
        method: "POST",
        url: "./api/analyze-image",
        contentType: "application/json",
        data: JSON.stringify({text: text })
      })
      .done(function(data) {
          // $('#input_imagen').hide();
          // $('#input_frase_all').hide();
          $('#banner-fig').hide();
          $('#input_imagen_arg').val("");
          $('#response').html(data);
          getHistory();
      });
    };

    //Retreive all the visitors from the database
    function getHistory(){
      $.get("./api/recent")
          .done(function(data) {
              if(data.length > 0) {
                $('#resultado_historial').html(data);
              }
          });
      }

      //Call getHistory on page load.
      getHistory();


$body = $("body");

$(document).on({
    ajaxStart: function() { $body.addClass("loading");    },
     ajaxStop: function() { $body.removeClass("loading"); }
});